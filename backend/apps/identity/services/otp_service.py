"""OTP generation, hashing, rate limiting, and verification service."""

from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.identity.models import OTPVerification, User
from apps.identity.providers.email_provider import get_email_provider
from apps.identity.providers.sms_provider import get_sms_provider

logger = logging.getLogger(__name__)


class OTPService:
    """Enterprise OTP verification lifecycle management."""

    EXPIRATION_MINUTES = 5
    COOLDOWN_SECONDS = 60
    MAX_ATTEMPTS = 3

    @staticmethod
    def _hash_otp(otp: str, target: str) -> str:
        """Compute salted SHA-256 hash of OTP string."""
        salt = target.strip().lower()
        return hashlib.sha256(f"{salt}:{otp}".encode()).hexdigest()

    @classmethod
    def request_otp(
        cls,
        target: str,
        channel: str,
        purpose: str,
        user: User | None = None,
    ) -> tuple[OTPVerification, str]:
        """Generate, record, and dispatch OTP to target channel.

        Returns the OTPVerification record and the plain-text OTP (for testing/delivery).
        """
        target = target.strip()
        channel = channel.lower()
        now = timezone.now()

        # Cooldown guard: Reject if active cooldown in effect
        recent_active = OTPVerification.objects.filter(
            target=target,
            channel=channel,
            purpose=purpose,
            cooldown_until__gt=now,
        ).first()
        if recent_active:
            remaining = int((recent_active.cooldown_until - now).total_seconds())
            raise ValidationError(
                f"Rate limit exceeded. Please wait {remaining} seconds before requesting a new OTP."
            )

        # Invalidate previous unused OTPs for the same target and purpose
        OTPVerification.objects.filter(
            target=target,
            channel=channel,
            purpose=purpose,
            is_used=False,
        ).update(is_used=True)

        # Generate cryptographic 6-digit numeric OTP
        plain_otp = f"{secrets.randbelow(1_000_000):06d}"
        otp_hash = cls._hash_otp(plain_otp, target)

        verification = OTPVerification.objects.create(
            user=user,
            target=target,
            channel=channel,
            purpose=purpose,
            otp_hash=otp_hash,
            attempts=0,
            max_attempts=cls.MAX_ATTEMPTS,
            is_used=False,
            expires_at=now + timedelta(minutes=cls.EXPIRATION_MINUTES),
            cooldown_until=now + timedelta(seconds=cls.COOLDOWN_SECONDS),
        )

        # Deliver via appropriate channel
        if channel == OTPVerification.CHANNEL_SMS:
            sms_provider = get_sms_provider()
            delivered = sms_provider.send_otp(target, plain_otp, purpose)
            if not delivered:
                logger.error("Failed to deliver SMS OTP to %s", target)
        elif channel == OTPVerification.CHANNEL_EMAIL:
            email_provider = get_email_provider()
            delivered = email_provider.send_otp(target, plain_otp, purpose)
            if not delivered:
                logger.error("Failed to deliver Email OTP to %s", target)
        else:
            raise ValidationError(f"Unsupported delivery channel: {channel}")

        return verification, plain_otp

    @classmethod
    def verify_otp(
        cls,
        target: str,
        channel: str,
        purpose: str,
        plain_otp: str,
    ) -> OTPVerification:
        """Validate provided OTP against active verification record."""
        target = target.strip()
        channel = channel.lower()
        now = timezone.now()

        verification = OTPVerification.objects.filter(
            target=target,
            channel=channel,
            purpose=purpose,
            is_used=False,
        ).order_by("-created_at").first()

        if not verification:
            raise ValidationError("No active OTP request found for this channel. Please request a new OTP.")

        if verification.expires_at < now:
            verification.is_used = True
            verification.save(update_fields=["is_used"])
            raise ValidationError("OTP has expired. Please request a new code.")

        if verification.attempts >= verification.max_attempts:
            verification.is_used = True
            verification.save(update_fields=["is_used"])
            raise ValidationError("Maximum verification attempts exceeded. Please request a new code.")

        expected_hash = cls._hash_otp(plain_otp.strip(), target)
        if not secrets.compare_digest(verification.otp_hash, expected_hash):
            verification.attempts += 1
            if verification.attempts >= verification.max_attempts:
                verification.is_used = True
                verification.save(update_fields=["attempts", "is_used"])
                raise ValidationError("Invalid OTP. Maximum attempts exceeded. Code invalidated.")
            verification.save(update_fields=["attempts"])
            raise ValidationError(
                f"Invalid OTP. {verification.max_attempts - verification.attempts} attempts remaining."
            )

        # Success - prevent replay
        verification.is_used = True
        verification.save(update_fields=["is_used"])

        # Update User verification status if user linked
        user = verification.user
        if not user:
            # Try to lookup user by email or phone
            if channel == OTPVerification.CHANNEL_EMAIL:
                user = User.objects.filter(email__iexact=target).first()
            elif channel == OTPVerification.CHANNEL_SMS:
                user = User.objects.filter(phone=target).first()

        if user:
            if channel == OTPVerification.CHANNEL_EMAIL:
                user.is_email_verified = True
            elif channel == OTPVerification.CHANNEL_SMS:
                user.is_mobile_verified = True
            user.save(update_fields=["is_email_verified", "is_mobile_verified", "updated_at"])

        return verification
