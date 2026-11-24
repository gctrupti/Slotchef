"""Cash on Delivery (COD) collection, household confirmation, dispute, and commission accrual."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditLog
from apps.bookings.models import Booking
from apps.cooks.models import CookProfile
from apps.finance.models import (
    CashCollectionRecord,
    CommissionLedger,
)
from apps.finance.services.pricing_calculator import PricingCalculatorService
from apps.identity.models import User


class CashService:
    """Manages visit cash collections, dispute lifecycle, and cook commission liability."""

    @classmethod
    def report_cash_collection(
        cls,
        booking: Booking,
        cook: CookProfile,
        reported_amount_minor_units: int,
        cook_notes: str = "",
    ) -> CashCollectionRecord:
        """Cook marks cash received directly from household."""
        if hasattr(booking, "cash_collection"):
            record = booking.cash_collection
            if record.status in [CashCollectionRecord.STATUS_CONFIRMED, CashCollectionRecord.STATUS_RESOLVED]:
                raise ValidationError("Cash collection for this booking is already confirmed/resolved.")
        else:
            record = None

        if not hasattr(booking, "price_breakdown"):
            PricingCalculatorService.calculate_price_breakdown(booking, persist=True)

        commission_owed = booking.price_breakdown.platform_commission_minor_units

        with transaction.atomic():
            now = timezone.now()
            if not record:
                record = CashCollectionRecord.objects.create(
                    booking=booking,
                    cook=cook,
                    household=booking.household,
                    reported_amount_minor_units=reported_amount_minor_units,
                    collected_at=now,
                    status=CashCollectionRecord.STATUS_REPORTED,
                    cook_notes=cook_notes,
                )
            else:
                record.reported_amount_minor_units = reported_amount_minor_units
                record.collected_at = now
                record.status = CashCollectionRecord.STATUS_REPORTED
                record.cook_notes = cook_notes
                record.save()

            # Record commission liability in ledger
            last_entry = CommissionLedger.objects.filter(cook=cook).order_by("-created_at").first()
            current_bal = last_entry.running_balance_minor_units if last_entry else 0
            new_bal = current_bal + commission_owed

            CommissionLedger.objects.create(
                cook=cook,
                booking=booking,
                entry_type=CommissionLedger.TYPE_COMMISSION_ACCRUED,
                amount_minor_units=commission_owed,
                running_balance_minor_units=new_bal,
                description=f"Commission accrued for COD visit on booking {booking.id}",
            )

            AuditLog.objects.create(
                actor=cook.user,
                action="CASH_REPORTED",
                entity_type="CashCollectionRecord",
                entity_id=str(record.id),
                after_state={
                    "reported_amount": reported_amount_minor_units,
                    "commission_liability": commission_owed,
                    "running_commission_balance": new_bal,
                },
            )

        return record

    @classmethod
    def confirm_cash_collection(
        cls,
        booking: Booking,
        household_user: User,
    ) -> CashCollectionRecord:
        """Household resident confirms that cash was physically paid to cook."""
        if not hasattr(booking, "cash_collection"):
            raise ValidationError("No cash collection recorded for this booking.")

        record = booking.cash_collection
        if record.status == CashCollectionRecord.STATUS_CONFIRMED:
            return record

        with transaction.atomic():
            record.status = CashCollectionRecord.STATUS_CONFIRMED
            record.save(update_fields=["status", "updated_at"])

            AuditLog.objects.create(
                actor=household_user,
                action="CASH_CONFIRMED",
                entity_type="CashCollectionRecord",
                entity_id=str(record.id),
                after_state={"status": record.status},
            )

        return record

    @classmethod
    def dispute_cash_collection(
        cls,
        booking: Booking,
        household_user: User,
        reason: str,
    ) -> CashCollectionRecord:
        """Household resident disputes reported cash collection."""
        if not hasattr(booking, "cash_collection"):
            raise ValidationError("No cash collection recorded for this booking.")

        record = booking.cash_collection

        with transaction.atomic():
            record.status = CashCollectionRecord.STATUS_DISPUTED
            record.household_dispute_reason = reason
            record.save(update_fields=["status", "household_dispute_reason", "updated_at"])

            AuditLog.objects.create(
                actor=household_user,
                action="CASH_DISPUTED",
                entity_type="CashCollectionRecord",
                entity_id=str(record.id),
                reason=reason,
                after_state={"status": record.status},
            )

        return record

    @classmethod
    def admin_resolve_dispute(
        cls,
        cash_record_id: str,
        resolved_amount_minor_units: int,
        admin_user: User,
        resolution_notes: str,
    ) -> CashCollectionRecord:
        """Administrator arbitrates cash dispute and adjusts commission ledger balance."""
        record = CashCollectionRecord.objects.select_related("cook", "booking").filter(id=cash_record_id).first()
        if not record:
            raise ValidationError("Cash collection record not found.")

        with transaction.atomic():
            record.status = CashCollectionRecord.STATUS_RESOLVED
            record.reported_amount_minor_units = resolved_amount_minor_units
            record.admin_resolution_notes = resolution_notes
            record.save(update_fields=["status", "reported_amount_minor_units", "admin_resolution_notes", "updated_at"])

            AuditLog.objects.create(
                actor=admin_user,
                action="CASH_DISPUTE_RESOLVED",
                entity_type="CashCollectionRecord",
                entity_id=str(record.id),
                reason=resolution_notes,
                after_state={"resolved_amount": resolved_amount_minor_units, "status": record.status},
            )

        return record

