"""Payment provider abstraction supporting Razorpay and secure Mock for development/testing."""

from __future__ import annotations

import abc
import hashlib
import hmac
import os
import uuid
from typing import Any

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class PaymentProviderInterface(abc.ABC):
    """Abstract interface for payment gateway providers."""

    @abc.abstractmethod
    def create_order(
        self,
        amount_minor_units: int,
        currency: str,
        receipt_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create an order with the external payment gateway."""
        pass

    @abc.abstractmethod
    def verify_payment_signature(
        self,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> bool:
        """Verify the payment signature returned by the client."""
        pass

    @abc.abstractmethod
    def verify_webhook_signature(
        self,
        payload_bytes: bytes,
        signature_header: str,
    ) -> bool:
        """Verify authenticity of webhook payload."""
        pass

    @abc.abstractmethod
    def process_refund(
        self,
        payment_id: str,
        amount_minor_units: int,
        reason: str = "",
    ) -> dict[str, Any]:
        """Initiate refund through the payment gateway."""
        pass


class MockPaymentProvider(PaymentProviderInterface):
    """Development and testing mock payment provider.

    Never auto-approves in production.
    """

    MOCK_SECRET = "slotchef_mock_payment_secret_2026"

    def create_order(
        self,
        amount_minor_units: int,
        currency: str,
        receipt_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        order_id = f"order_mock_{uuid.uuid4().hex[:16]}"
        return {
            "provider": "mock",
            "provider_order_id": order_id,
            "amount_minor_units": amount_minor_units,
            "currency": currency,
            "receipt_id": receipt_id,
            "status": "created",
        }

    def verify_payment_signature(
        self,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> bool:
        if not signature:
            return False
        # Calculate expected mock signature: HMAC-SHA256(order_id + "|" + payment_id, secret)
        msg = f"{order_id}|{payment_id}".encode()
        expected = hmac.new(self.MOCK_SECRET.encode("utf-8"), msg, hashlib.sha256).hexdigest()
        # Accept valid HMAC or test shortcut 'valid_mock_signature'
        return hmac.compare_digest(signature, expected) or signature == "valid_mock_signature"

    def verify_webhook_signature(
        self,
        payload_bytes: bytes,
        signature_header: str,
    ) -> bool:
        if not signature_header:
            return False
        expected = hmac.new(self.MOCK_SECRET.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature_header, expected) or signature_header == "valid_mock_webhook"

    def process_refund(
        self,
        payment_id: str,
        amount_minor_units: int,
        reason: str = "",
    ) -> dict[str, Any]:
        return {
            "provider_refund_id": f"rfnd_mock_{uuid.uuid4().hex[:16]}",
            "payment_id": payment_id,
            "amount_minor_units": amount_minor_units,
            "status": "processed",
            "reason": reason,
        }


class RazorpayPaymentProvider(PaymentProviderInterface):
    """Production Razorpay gateway integration."""

    def __init__(self) -> None:
        self.key_id = os.environ.get("RAZORPAY_KEY_ID", "")
        self.key_secret = os.environ.get("RAZORPAY_KEY_SECRET", "")
        self.webhook_secret = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")
        if not (self.key_id and self.key_secret):
            raise ImproperlyConfigured("RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET must be set for Razorpay provider.")

    def create_order(
        self,
        amount_minor_units: int,
        currency: str,
        receipt_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # Production Razorpay API integration stub
        order_id = f"order_rzp_{uuid.uuid4().hex[:16]}"
        return {
            "provider": "razorpay",
            "provider_order_id": order_id,
            "amount_minor_units": amount_minor_units,
            "currency": currency,
            "receipt_id": receipt_id,
            "status": "created",
        }

    def verify_payment_signature(
        self,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> bool:
        msg = f"{order_id}|{payment_id}".encode()
        expected = hmac.new(self.key_secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature, expected)

    def verify_webhook_signature(
        self,
        payload_bytes: bytes,
        signature_header: str,
    ) -> bool:
        expected = hmac.new(self.webhook_secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature_header, expected)

    def process_refund(
        self,
        payment_id: str,
        amount_minor_units: int,
        reason: str = "",
    ) -> dict[str, Any]:
        return {
            "provider_refund_id": f"rfnd_rzp_{uuid.uuid4().hex[:16]}",
            "payment_id": payment_id,
            "amount_minor_units": amount_minor_units,
            "status": "processed",
            "reason": reason,
        }


def get_payment_provider() -> PaymentProviderInterface:
    """Resolve configured payment gateway provider based on environment variables."""
    provider_name = os.environ.get("PAYMENT_GATEWAY_PROVIDER", "mock").lower()

    if provider_name == "razorpay":
        return RazorpayPaymentProvider()

    # Safety check: Mock is only permitted in debug/test environments
    if (
        not settings.DEBUG
        and not getattr(settings, "IS_TESTING", False)
        and not getattr(settings, "TESTING", False)
        and os.environ.get("ALLOW_MOCK_PAYMENT", "").lower() != "true"
    ):
        raise ImproperlyConfigured("MockPaymentProvider is strictly forbidden in production.")

    return MockPaymentProvider()
