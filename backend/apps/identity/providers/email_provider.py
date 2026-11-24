"""Email provider abstraction for OTP and alert delivery across all SlotChef portals."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


class EmailProviderInterface(ABC):
    """Abstract interface for sending Email OTP messages."""

    @abstractmethod
    def send_otp(self, email: str, otp: str, purpose: str) -> bool:
        """Deliver one-time password to the target email address."""
        pass


class MockEmailProvider(EmailProviderInterface):
    """Development and test mock email provider. Strictly forbidden in production."""

    sent_emails: list[dict[str, Any]] = []

    def __init__(self) -> None:
        if not settings.DEBUG and not getattr(settings, "IS_TESTING", False):
            raise RuntimeError("MockEmailProvider is strictly forbidden in production environments.")

    def send_otp(self, email: str, otp: str, purpose: str) -> bool:
        if not settings.DEBUG and not getattr(settings, "IS_TESTING", False):
            raise RuntimeError("MockEmailProvider is strictly forbidden in production environments.")

        record = {
            "email": email,
            "otp": otp,
            "purpose": purpose,
        }
        self.sent_emails.append(record)
        logger.info("Mock Email sent to %s for purpose %s: OTP %s", email, purpose, otp)
        return True


class DjangoEmailProvider(EmailProviderInterface):
    """Production email provider utilizing standard Django SMTP / SES backend."""

    def send_otp(self, email: str, otp: str, purpose: str) -> bool:
        subject = f"SlotChef Verification Code: {otp}"
        message = (
            f"Hello,\n\n"
            f"Your SlotChef verification code is: {otp}\n"
            f"This code will expire in 5 minutes.\n"
            f"If you did not request this code, please ignore this email.\n\n"
            f"Team SlotChef"
        )
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@slotchef.com")

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[email],
                fail_silently=False,
            )
            return True
        except Exception as exc:
            logger.exception("Failed to dispatch email via Django mail backend: %s", exc)
            return False


def get_email_provider() -> EmailProviderInterface:
    """Return configured Email provider instance."""
    provider_name = getattr(settings, "SLOTCHEF_EMAIL_PROVIDER", "mock").lower()
    if provider_name == "smtp" or provider_name == "django":
        return DjangoEmailProvider()
    return MockEmailProvider()

