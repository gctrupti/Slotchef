"""Identity, user, and role models for SlotChef."""

from __future__ import annotations

import uuid
from typing import Any

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models


class UserManager(BaseUserManager):
    """Custom user manager where email is the unique identifier for auth."""

    def create_user(
        self,
        email: str,
        password: str | None = None,
        **extra_fields: Any,
    ) -> User:
        if not email:
            raise ValueError("The Email field must be set.")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        password: str | None = None,
        **extra_fields: Any,
    ) -> User:
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Core user entity with UUID primary key and email login."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    phone = models.CharField(max_length=32, blank=True, default="")
    first_name = models.CharField(max_length=150, blank=True, default="")
    last_name = models.CharField(max_length=150, blank=True, default="")
    legal_name = models.CharField(max_length=255, blank=True, default="")
    is_email_verified = models.BooleanField(default=False, db_index=True)
    is_mobile_verified = models.BooleanField(default=False, db_index=True)
    mfa_enabled = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        db_table = "identity_user"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email"], name="idx_user_email"),
        ]

    def __str__(self) -> str:
        return self.email

    def has_role(self, role_code: str) -> bool:
        """Check if user has a specific assigned role."""
        if self.is_superuser:
            return True
        return self.user_roles.filter(role__code=role_code).exists()

    @property
    def is_fully_verified(self) -> bool:
        """True when both email and mobile channels are verified."""
        return self.is_email_verified and self.is_mobile_verified


class Role(models.Model):
    """System and domain roles (household_member, cook, society_admin, platform_admin)."""

    HOUSEHOLD_MEMBER = "household_member"
    COOK = "cook"
    SOCIETY_ADMIN = "society_admin"
    PLATFORM_ADMIN = "platform_admin"

    ROLE_CHOICES = (
        (HOUSEHOLD_MEMBER, "Household Member"),
        (COOK, "Cook"),
        (SOCIETY_ADMIN, "Society Administrator"),
        (PLATFORM_ADMIN, "Platform Administrator"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=64, unique=True, choices=ROLE_CHOICES)
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "identity_role"
        ordering = ["code"]

    def __str__(self) -> str:
        return self.name


class UserRole(models.Model):
    """Explicit junction between users and granted roles."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_roles")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="user_roles")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "identity_user_role"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "role"],
                name="unique_user_role",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user.email} -> {self.role.code}"


class OTPVerification(models.Model):
    """Secure hashed OTP verification tokens with rate limiting and cooldown."""

    CHANNEL_SMS = "sms"
    CHANNEL_EMAIL = "email"

    CHANNEL_CHOICES = (
        (CHANNEL_SMS, "SMS"),
        (CHANNEL_EMAIL, "Email"),
    )

    PURPOSE_REGISTRATION = "registration"
    PURPOSE_LOGIN = "login"
    PURPOSE_ADMIN_MFA = "admin_mfa"
    PURPOSE_PASSWORD_RESET = "password_reset"
    PURPOSE_CONTACT_CHANGE = "contact_change"

    PURPOSE_CHOICES = (
        (PURPOSE_REGISTRATION, "Registration Verification"),
        (PURPOSE_LOGIN, "Login Authentication"),
        (PURPOSE_ADMIN_MFA, "Admin MFA Step-up"),
        (PURPOSE_PASSWORD_RESET, "Password Reset"),
        (PURPOSE_CONTACT_CHANGE, "Contact Change Verification"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="otp_verifications",
    )
    target = models.CharField(max_length=255, db_index=True, help_text="Email or Phone target")
    channel = models.CharField(max_length=16, choices=CHANNEL_CHOICES)
    purpose = models.CharField(max_length=32, choices=PURPOSE_CHOICES, default=PURPOSE_LOGIN)
    otp_hash = models.CharField(max_length=128, help_text="SHA-256 hashed OTP")
    attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=3)
    is_used = models.BooleanField(default=False, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    cooldown_until = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "identity_otp_verification"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["target", "purpose", "is_used"], name="idx_otp_target_purpose"),
        ]

    def __str__(self) -> str:
        return f"OTP [{self.channel}] for {self.target} ({self.purpose}) [Used: {self.is_used}]"


class AdminInvitation(models.Model):
    """Signed invitations for administrative account provisioning."""

    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"
    STATUS_REVOKED = "revoked"
    STATUS_EXPIRED = "expired"

    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_ACCEPTED, "Accepted"),
        (STATUS_REVOKED, "Revoked"),
        (STATUS_EXPIRED, "Expired"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    role = models.ForeignKey(Role, on_delete=models.PROTECT)
    invited_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="sent_admin_invitations")
    token_hash = models.CharField(max_length=128, unique=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_PENDING)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "identity_admin_invitation"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Invitation for {self.email} ({self.role.code}) [{self.status}]"


class LoginAttempt(models.Model):
    """Persistent tracking of failed authentication attempts for brute-force defense."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    identifier = models.CharField(max_length=255, db_index=True, help_text="Email, phone, or username attempted")
    ip_address = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    failed_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True, db_index=True)
    last_attempt_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "identity_login_attempt"
        indexes = [
            models.Index(fields=["identifier", "locked_until"], name="idx_login_attempt_lock"),
        ]

    def __str__(self) -> str:
        return f"LoginAttempt for {self.identifier} (Failed: {self.failed_attempts})"

