"""Service managing online payment orders, verification, refunds, and webhooks."""

from __future__ import annotations

import json
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.audit.models import AuditLog
from apps.bookings.models import Booking, HouseholdPackageSubscription
from apps.finance.models import (
    PaymentOrder,
    PaymentTransaction,
    RefundRecord,
)
from apps.finance.providers.payment_provider import get_payment_provider
from apps.finance.services.pricing_calculator import PricingCalculatorService
from apps.households.models import Household


class PaymentService:
    """Manages online payment order lifecycle, signature verification, and refunds."""

    @classmethod
    def create_payment_order(
        cls,
        household: Household,
        booking: Booking | None = None,
        subscription: HouseholdPackageSubscription | None = None,
        idempotency_key: str = "",
    ) -> PaymentOrder:
        """Create payment order with payment gateway provider."""
        if not booking and not subscription:
            raise ValidationError("Either a booking or subscription must be specified for payment.")

        # Check existing order with same idempotency key
        if idempotency_key:
            existing = PaymentOrder.objects.filter(idempotency_key=idempotency_key).first()
            if existing:
                return existing

        amount = 0
        currency = "INR"
        receipt_id = f"rcpt_{booking.id if booking else subscription.id}"

        if booking:
            if not hasattr(booking, "price_breakdown"):
                PricingCalculatorService.calculate_price_breakdown(booking, persist=True)
            amount = booking.price_breakdown.total_amount_minor_units
            currency = booking.price_breakdown.currency
        elif subscription:
            amount = subscription.package_plan.price_minor_units
            currency = subscription.package_plan.currency

        provider = get_payment_provider()
        provider_resp = provider.create_order(
            amount_minor_units=amount,
            currency=currency,
            receipt_id=receipt_id,
        )

        with transaction.atomic():
            order = PaymentOrder.objects.create(
                household=household,
                booking=booking,
                subscription=subscription,
                amount_minor_units=amount,
                currency=currency,
                provider=provider_resp.get("provider", "mock"),
                provider_order_id=provider_resp["provider_order_id"],
                status=PaymentOrder.STATUS_CREATED,
                idempotency_key=idempotency_key,
            )

            AuditLog.objects.create(
                action="PAYMENT_ORDER_CREATED",
                entity_type="PaymentOrder",
                entity_id=str(order.id),
                after_state={
                    "provider_order_id": order.provider_order_id,
                    "amount": order.amount_minor_units,
                    "currency": order.currency,
                },
            )

        return order

    @classmethod
    def verify_and_confirm_payment(
        cls,
        order_id: str,
        provider_payment_id: str,
        signature: str,
        payment_method: str = "card",
        raw_payload: dict[str, Any] | None = None,
    ) -> PaymentTransaction:
        """Verify payment signature and finalize order transaction."""
        order = PaymentOrder.objects.filter(provider_order_id=order_id).first()
        if not order:
            raise ValidationError(f"Payment order '{order_id}' not found.")

        # Idempotency: if already paid, return latest successful transaction
        if order.status == PaymentOrder.STATUS_PAID:
            txn = order.transactions.filter(status=PaymentTransaction.STATUS_SUCCESS).first()
            if txn:
                return txn

        provider = get_payment_provider()
        is_valid = provider.verify_payment_signature(
            order_id=order_id,
            payment_id=provider_payment_id,
            signature=signature,
        )

        with transaction.atomic():
            if not is_valid:
                txn = PaymentTransaction.objects.create(
                    payment_order=order,
                    provider_payment_id=provider_payment_id,
                    amount_minor_units=order.amount_minor_units,
                    status=PaymentTransaction.STATUS_FAILED,
                    payment_method=payment_method,
                    signature=signature,
                    error_code="INVALID_SIGNATURE",
                    error_description="Signature verification failed.",
                    raw_payload=raw_payload or {},
                )
                order.status = PaymentOrder.STATUS_FAILED
                order.save(update_fields=["status", "updated_at"])
                raise ValidationError("Payment signature verification failed.")

            txn = PaymentTransaction.objects.create(
                payment_order=order,
                provider_payment_id=provider_payment_id,
                amount_minor_units=order.amount_minor_units,
                status=PaymentTransaction.STATUS_SUCCESS,
                payment_method=payment_method,
                signature=signature,
                raw_payload=raw_payload or {},
            )
            order.status = PaymentOrder.STATUS_PAID
            order.save(update_fields=["status", "updated_at"])

            AuditLog.objects.create(
                action="PAYMENT_VERIFIED_SUCCESS",
                entity_type="PaymentTransaction",
                entity_id=str(txn.id),
                after_state={
                    "order_id": order.provider_order_id,
                    "payment_id": provider_payment_id,
                    "amount": txn.amount_minor_units,
                },
            )

        return txn

    @classmethod
    def process_webhook_event(
        cls,
        payload_bytes: bytes,
        signature_header: str,
    ) -> dict[str, Any]:
        """Validate and process incoming webhook event payload."""
        provider = get_payment_provider()
        if not provider.verify_webhook_signature(payload_bytes, signature_header):
            raise ValidationError("Invalid webhook signature.")

        payload = json.loads(payload_bytes.decode("utf-8"))
        event_type = payload.get("event", "payment.captured")

        # Process standard payment captured event
        if "payment" in event_type:
            payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
            order_id = payment_entity.get("order_id")
            payment_id = payment_entity.get("id")
            if order_id and payment_id:
                order = PaymentOrder.objects.filter(provider_order_id=order_id).first()
                if order and order.status != PaymentOrder.STATUS_PAID:
                    cls.verify_and_confirm_payment(
                        order_id=order_id,
                        provider_payment_id=payment_id,
                        signature="webhook_verified",
                        raw_payload=payload,
                    )

        return {"status": "processed", "event": event_type}

    @classmethod
    def issue_refund(
        cls,
        transaction_id: str,
        amount_minor_units: int | None = None,
        reason: str = "",
    ) -> RefundRecord:
        """Issue full or partial refund against successful online payment."""
        txn = PaymentTransaction.objects.filter(id=transaction_id).first()
        if not txn:
            raise ValidationError(f"Transaction '{transaction_id}' not found.")
        if txn.status != PaymentTransaction.STATUS_SUCCESS:
            raise ValidationError("Only successful transactions can be refunded.")

        refund_amount = amount_minor_units or txn.amount_minor_units
        if refund_amount > txn.amount_minor_units or refund_amount <= 0:
            raise ValidationError(f"Invalid refund amount: {refund_amount}")

        provider = get_payment_provider()
        provider_resp = provider.process_refund(
            payment_id=txn.provider_payment_id,
            amount_minor_units=refund_amount,
            reason=reason,
        )

        with transaction.atomic():
            refund = RefundRecord.objects.create(
                payment_transaction=txn,
                amount_minor_units=refund_amount,
                reason=reason,
                provider_refund_id=provider_resp.get("provider_refund_id", ""),
                status=RefundRecord.STATUS_PROCESSED,
            )
            txn.status = PaymentTransaction.STATUS_REFUNDED
            txn.save(update_fields=["status"])

            AuditLog.objects.create(
                action="PAYMENT_REFUNDED",
                entity_type="RefundRecord",
                entity_id=str(refund.id),
                after_state={
                    "transaction_id": str(txn.id),
                    "amount": refund_amount,
                    "reason": reason,
                },
            )

        return refund

