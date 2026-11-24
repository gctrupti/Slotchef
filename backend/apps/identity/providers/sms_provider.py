"""SMS provider abstraction for OTP delivery across all SlotChef portals."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)


class SMSProviderInterface(ABC):
    """Abstract interface for sending SMS OTP messages."""

    @abstractmethod
    def send_otp(self, phone: str, otp: str, purpose: str) -> bool:
        """Deliver one-time password to the target mobile phone number."""
        pass


class MockSMSProvider(SMSProviderInterface):
    """Development and test mock SMS provider. Strictly forbidden in production."""

    sent_messages: list[dict[str, Any]] = []

    def __init__(self) -> None:
        if not settings.DEBUG and not getattr(settings, "IS_TESTING", False):
            raise RuntimeError("MockSMSProvider is strictly forbidden in production environments.")

    def send_otp(self, phone: str, otp: str, purpose: str) -> bool:
        if not settings.DEBUG and not getattr(settings, "IS_TESTING", False):
            raise RuntimeError("MockSMSProvider is strictly forbidden in production environments.")

        message = {
            "phone": phone,
            "otp": otp,
            "purpose": purpose,
        }
        self.sent_messages.append(message)
        logger.info("Mock SMS sent to %s for purpose %s: OTP %s", phone, purpose, otp)
        return True


class TwilioSMSProvider(SMSProviderInterface):
    """Twilio SMS provider using configured API credentials."""

    def __init__(self) -> None:
        self.account_sid = getattr(settings, "TWILIO_ACCOUNT_SID", "")
        self.auth_token = getattr(settings, "TWILIO_AUTH_TOKEN", "")
        self.from_number = getattr(settings, "TWILIO_FROM_NUMBER", "")

    def send_otp(self, phone: str, otp: str, purpose: str) -> bool:
        if not self.account_sid or not self.auth_token or not self.from_number:
            logger.error("Twilio credentials not fully configured in environment.")
            return False

        try:
            # Staged Twilio client invocation via standard REST client
            import base64
            import urllib.parse
            import urllib.request

            auth_str = f"{self.account_sid}:{self.auth_token}"
            b64_auth = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"

            body = f"Your SlotChef verification code is {otp}. Valid for 5 minutes. Do not share."
            data = urllib.parse.urlencode({
                "To": phone,
                "From": self.from_number,
                "Body": body,
            }).encode("utf-8")

            req = urllib.request.Request(
                url,
                data=data,
                headers={"Authorization": f"Basic {b64_auth}"},
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.status in (200, 201)
        except Exception as exc:
            logger.exception("Failed to dispatch SMS via Twilio: %s", exc)
            return False


def get_sms_provider() -> SMSProviderInterface:
    """Return configured SMS provider instance."""
    provider_name = getattr(settings, "SLOTCHEF_SMS_PROVIDER", "mock").lower()
    if provider_name == "twilio":
        return TwilioSMSProvider()
    return MockSMSProvider()
