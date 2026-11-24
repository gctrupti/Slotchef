"""Enterprise authentication service managing brute-force protection, lockout, and Admin MFA."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import jwt
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.audit.models import AuditLog
from apps.identity.models import LoginAttempt, OTPVerification, Role, User
from apps.identity.services.otp_service import OTPService

logger = logging.getLogger(__name__)


class AuthService:
    """Manages login attempt rate-limiting, account lockouts, and multi-factor step-up authentication."""

    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_MINUTES = 15

    @classmethod
    def check_lockout(cls, identifier: str) -> tuple[bool, int]:
        """Check if target identifier is currently locked out from login.

        Returns (is_locked, remaining_minutes).
        """
        cleaned = identifier.strip().lower()
        now = timezone.now()

        attempt = LoginAttempt.objects.filter(identifier=cleaned).first()
        if not attempt:
            return False, 0

        if attempt.locked_until and attempt.locked_until > now:
            remaining = int((attempt.locked_until - now).total_seconds() // 60) + 1
            return True, remaining

        # If lockout expired, reset state
        if attempt.locked_until and attempt.locked_until <= now:
            attempt.failed_attempts = 0
            attempt.locked_until = None
            attempt.save(update_fields=["failed_attempts", "locked_until"])

        return False, 0

    @classmethod
    def record_login_failure(cls, identifier: str, ip_address: str | None = None) -> tuple[int, bool, int]:
        """Record a failed login credential attempt.

        Returns (failed_attempts, is_now_locked, lockout_minutes).
        """
        cleaned = identifier.strip().lower()
        now = timezone.now()

        attempt, _ = LoginAttempt.objects.get_or_create(identifier=cleaned)
        if ip_address:
            attempt.ip_address = ip_address

        attempt.failed_attempts += 1
        is_locked = False
        remaining_minutes = 0

        if attempt.failed_attempts >= cls.MAX_FAILED_ATTEMPTS:
            attempt.locked_until = now + timedelta(minutes=cls.LOCKOUT_MINUTES)
            is_locked = True
            remaining_minutes = cls.LOCKOUT_MINUTES

            AuditLog.objects.create(
                action="auth.account_locked",
                entity_type="LoginAttempt",
                entity_id=cleaned,
                after_state={
                    "identifier": cleaned,
                    "failed_attempts": attempt.failed_attempts,
                    "locked_until": attempt.locked_until.isoformat(),
                    "ip_address": ip_address,
                },
            )
            logger.warning("Account/identifier %s locked out for %d minutes due to repeated failures.", cleaned, cls.LOCKOUT_MINUTES)

        attempt.save()
        return attempt.failed_attempts, is_locked, remaining_minutes

    @classmethod
    def clear_login_failures(cls, identifier: str) -> None:
        """Reset failed attempt counters upon successful authentication."""
        cleaned = identifier.strip().lower()
        LoginAttempt.objects.filter(identifier=cleaned).update(failed_attempts=0, locked_until=None)

    @classmethod
    def create_admin_mfa_challenge(cls, user: User) -> dict[str, Any]:
        """Generate and dispatch MFA challenge for administrator login."""
        if not (user.is_superuser or user.has_role(Role.PLATFORM_ADMIN) or user.has_role(Role.SOCIETY_ADMIN)):
            raise ValidationError("MFA challenges are restricted to administrative accounts.")

        # Dispatch OTP to admin email
        verification, _ = OTPService.request_otp(
            target=user.email,
            channel=OTPVerification.CHANNEL_EMAIL,
            purpose=OTPVerification.PURPOSE_ADMIN_MFA,
            user=user,
        )

        # Generate temporary signed MFA token
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "action": "admin_mfa",
            "exp": timezone.now() + timedelta(minutes=5),
        }
        secret = settings.SECRET_KEY
        mfa_token = jwt.encode(payload, secret, algorithm="HS256")

        return {
            "mfa_required": True,
            "mfa_token": mfa_token,
            "channel": "email",
            "target": user.email,
            "expires_in_seconds": 300,
        }

    @classmethod
    def verify_admin_mfa_challenge(cls, mfa_token: str, otp: str) -> User:
        """Validate MFA challenge token and OTP verification code."""
        secret = settings.SECRET_KEY
        try:
            payload = jwt.decode(mfa_token, secret, algorithms=["HS256"])
        except jwt.PyJWTError as exc:
            raise ValidationError(f"Invalid or expired MFA session token: {exc}") from exc

        if payload.get("action") != "admin_mfa":
            raise ValidationError("Invalid MFA token action.")

        user_id = payload.get("sub")
        user = User.objects.filter(id=user_id, is_active=True).first()
        if not user:
            raise ValidationError("User associated with MFA session not found or inactive.")

        # Verify OTP
        OTPService.verify_otp(
            target=user.email,
            channel=OTPVerification.CHANNEL_EMAIL,
            purpose=OTPVerification.PURPOSE_ADMIN_MFA,
            plain_otp=otp,
        )

        AuditLog.objects.create(
            actor=user,
            action="auth.admin_mfa_successful",
            entity_type="User",
            entity_id=str(user.id),
            after_state={"email": user.email},
        )
        return user

