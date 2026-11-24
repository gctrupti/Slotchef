"""Serializers for Identity domain (registration, password & dual-identifier login, OTP, admin, contact change)."""

from __future__ import annotations

import contextlib
from typing import Any

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.identity.models import AdminInvitation, OTPVerification, Role, User, UserRole
from apps.identity.services.auth_service import AuthService
from apps.identity.services.otp_service import OTPService


class UserSerializer(serializers.ModelSerializer):
    """Public user serializer with assigned roles and verification status."""

    roles = serializers.SerializerMethodField()
    is_fully_verified = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "phone",
            "first_name",
            "last_name",
            "legal_name",
            "roles",
            "is_email_verified",
            "is_mobile_verified",
            "is_fully_verified",
            "mfa_enabled",
            "is_active",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "roles",
            "is_email_verified",
            "is_mobile_verified",
            "is_fully_verified",
            "is_active",
            "created_at",
        ]

    def get_roles(self, obj: User) -> list[str]:
        return list(obj.user_roles.values_list("role__code", flat=True))


class RegisterSerializer(serializers.Serializer):
    """User registration serializer enforcing strict role segregation and initial channel OTP dispatch."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    phone = serializers.CharField(required=False, allow_blank=True, default="")
    first_name = serializers.CharField(required=False, allow_blank=True, default="")
    last_name = serializers.CharField(required=False, allow_blank=True, default="")
    legal_name = serializers.CharField(required=False, allow_blank=True, default="")
    role = serializers.ChoiceField(
        choices=[Role.HOUSEHOLD_MEMBER, Role.COOK],
        default=Role.HOUSEHOLD_MEMBER,
        help_text="Public registration is strictly restricted to household_member and cook roles.",
    )
    verification_channel = serializers.ChoiceField(
        choices=OTPVerification.CHANNEL_CHOICES,
        required=False,
        help_text="Target channel for initial registration OTP delivery (sms or email).",
    )

    def validate_email(self, value: str) -> str:
        lowered = value.strip().lower()
        if User.objects.filter(email=lowered).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return lowered

    def validate_phone(self, value: str) -> str:
        cleaned = value.strip()
        if cleaned and User.objects.filter(phone=cleaned).exists():
            raise serializers.ValidationError("A user with this phone number already exists.")
        return cleaned

    def validate_role(self, value: str) -> str:
        if value in (Role.PLATFORM_ADMIN, Role.SOCIETY_ADMIN):
            raise serializers.ValidationError("Administrative accounts cannot be self-registered.")
        return value

    def validate_password(self, value: str) -> str:
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value

    def create(self, validated_data: dict[str, Any]) -> User:
        role_code = validated_data.pop("role", Role.HOUSEHOLD_MEMBER)
        channel = validated_data.pop("verification_channel", None)
        password = validated_data.pop("password")

        user = User.objects.create_user(
            password=password,
            is_email_verified=False,
            is_mobile_verified=False,
            **validated_data,
        )

        role, _ = Role.objects.get_or_create(
            code=role_code,
            defaults={"name": role_code.replace("_", " ").title()},
        )
        UserRole.objects.create(user=user, role=role)

        if role_code == Role.COOK:
            from apps.cooks.models import CookProfile, CookWorkPolicy
            cook_profile = CookProfile.objects.create(user=user)
            CookWorkPolicy.objects.create(cook=cook_profile)

        # Determine target channel for initial verification OTP
        selected_channel = channel or (OTPVerification.CHANNEL_SMS if user.phone else OTPVerification.CHANNEL_EMAIL)
        target = user.phone if selected_channel == OTPVerification.CHANNEL_SMS else user.email

        with contextlib.suppress(Exception):
            OTPService.request_otp(
                target=target,
                channel=selected_channel,
                purpose=OTPVerification.PURPOSE_REGISTRATION,
                user=user,
            )

        user._selected_verification_channel = selected_channel
        user._verification_target = target
        return user


class RegisterVerifyOTPSerializer(serializers.Serializer):
    """Verify registration OTP code and complete initial registration."""

    target = serializers.CharField(help_text="Registered email address or mobile phone number")
    channel = serializers.ChoiceField(choices=OTPVerification.CHANNEL_CHOICES)
    otp = serializers.CharField(min_length=6, max_length=6)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        target = attrs.get("target", "").strip()
        channel = attrs.get("channel")
        otp = attrs.get("otp", "").strip()

        # Find user
        user = None
        if channel == OTPVerification.CHANNEL_EMAIL:
            user = User.objects.filter(email__iexact=target).first()
        elif channel == OTPVerification.CHANNEL_SMS:
            user = User.objects.filter(phone=target).first()

        if not user:
            raise serializers.ValidationError({"target": "No registration found for this contact."})

        try:
            OTPService.verify_otp(
                target=target,
                channel=channel,
                purpose=OTPVerification.PURPOSE_REGISTRATION,
                plain_otp=otp,
            )
        except DjangoValidationError as err:
            raise serializers.ValidationError({"otp": str(err.message if hasattr(err, "message") else err)}) from err

        user.refresh_from_db()
        attrs["user"] = user
        return attrs


class LoginSerializer(serializers.Serializer):
    """User login supporting registered mobile number OR registered email + password with brute-force protection."""

    identifier = serializers.CharField(
        required=False,
        help_text="Registered email address or mobile phone number",
    )
    email = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        raw_identifier = attrs.get("identifier") or attrs.get("email") or ""
        identifier = str(raw_identifier).strip()
        password = attrs.get("password")

        if not identifier:
            raise serializers.ValidationError({"identifier": "Email or mobile number is required."})

        # 1. Check brute force lockout
        is_locked, remaining_minutes = AuthService.check_lockout(identifier)
        if is_locked:
            raise serializers.ValidationError(
                {"detail": f"Account is temporarily locked due to repeated failed login attempts. Please try again in {remaining_minutes} minutes."},
                code="account_locked",
            )

        # 2. Authenticate using dual EmailOrPhoneBackend
        user = authenticate(username=identifier, password=password)
        if not user or not user.is_active:
            failed_count, is_now_locked, lock_mins = AuthService.record_login_failure(identifier)
            if is_now_locked:
                raise serializers.ValidationError(
                    {"detail": f"Invalid credentials. Maximum attempts exceeded. Account is now locked for {lock_mins} minutes."},
                    code="account_locked",
                )
            remaining = AuthService.MAX_FAILED_ATTEMPTS - failed_count
            raise serializers.ValidationError(
                {"detail": f"Invalid credentials or inactive account. {remaining} attempt(s) remaining before temporary lockout."},
                code="authentication_failed",
            )

        # 3. Clear failure counters upon successful authentication
        AuthService.clear_login_failures(identifier)

        # 4. Check Admin MFA Requirement
        is_admin = user.is_superuser or user.has_role(Role.PLATFORM_ADMIN) or user.has_role(Role.SOCIETY_ADMIN)
        if is_admin and user.mfa_enabled:
            attrs["mfa_required"] = True
            attrs["mfa_challenge"] = AuthService.create_admin_mfa_challenge(user)
        else:
            attrs["mfa_required"] = False

        attrs["user"] = user
        return attrs


class AdminMFAVerifySerializer(serializers.Serializer):
    """Complete Admin MFA step-up verification."""

    mfa_token = serializers.CharField()
    otp = serializers.CharField(min_length=6, max_length=6)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        mfa_token = attrs.get("mfa_token", "").strip()
        otp = attrs.get("otp", "").strip()

        try:
            user = AuthService.verify_admin_mfa_challenge(mfa_token, otp)
        except DjangoValidationError as err:
            raise serializers.ValidationError({"otp": str(err.message if hasattr(err, "message") else err)}) from err

        attrs["user"] = user
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    """Request a password reset OTP for registered mobile or email."""

    target = serializers.CharField(help_text="Registered email address or mobile phone number")
    channel = serializers.ChoiceField(choices=OTPVerification.CHANNEL_CHOICES)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        target = attrs.get("target", "").strip()
        channel = attrs.get("channel")

        user = None
        if channel == OTPVerification.CHANNEL_EMAIL:
            user = User.objects.filter(email__iexact=target).first()
            if not user or not user.is_email_verified:
                raise serializers.ValidationError({"target": "No verified account associated with this email address."})
        elif channel == OTPVerification.CHANNEL_SMS:
            user = User.objects.filter(phone=target).first()
            if not user or not user.is_mobile_verified:
                raise serializers.ValidationError({"target": "No verified account associated with this phone number."})

        attrs["user"] = user
        return attrs


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Confirm password reset with OTP verification."""

    target = serializers.CharField()
    channel = serializers.ChoiceField(choices=OTPVerification.CHANNEL_CHOICES)
    otp = serializers.CharField(min_length=6, max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value: str) -> str:
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        target = attrs.get("target", "").strip()
        channel = attrs.get("channel")
        otp = attrs.get("otp", "").strip()

        user = None
        if channel == OTPVerification.CHANNEL_EMAIL:
            user = User.objects.filter(email__iexact=target).first()
        elif channel == OTPVerification.CHANNEL_SMS:
            user = User.objects.filter(phone=target).first()

        if not user:
            raise serializers.ValidationError({"target": "No user account associated with this target."})

        try:
            OTPService.verify_otp(
                target=target,
                channel=channel,
                purpose=OTPVerification.PURPOSE_PASSWORD_RESET,
                plain_otp=otp,
            )
        except DjangoValidationError as err:
            raise serializers.ValidationError({"otp": str(err.message if hasattr(err, "message") else err)}) from err

        attrs["user"] = user
        return attrs


class ContactChangeRequestSerializer(serializers.Serializer):
    """Request updating contact email or phone requiring verification on the new target."""

    new_target = serializers.CharField(help_text="New email address or mobile phone number")
    channel = serializers.ChoiceField(choices=OTPVerification.CHANNEL_CHOICES)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        new_target = attrs.get("new_target", "").strip()
        channel = attrs.get("channel")

        if channel == OTPVerification.CHANNEL_EMAIL:
            lowered = new_target.lower()
            if User.objects.filter(email=lowered).exists():
                raise serializers.ValidationError({"new_target": "Another account already uses this email address."})
            attrs["new_target"] = lowered
        elif channel == OTPVerification.CHANNEL_SMS and User.objects.filter(phone=new_target).exists():
            raise serializers.ValidationError({"new_target": "Another account already uses this phone number."})

        return attrs


class ContactChangeConfirmSerializer(serializers.Serializer):
    """Confirm updating contact email or phone with OTP verified on the new target."""

    new_target = serializers.CharField()
    channel = serializers.ChoiceField(choices=OTPVerification.CHANNEL_CHOICES)
    otp = serializers.CharField(min_length=6, max_length=6)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        new_target = attrs.get("new_target", "").strip()
        channel = attrs.get("channel")
        otp = attrs.get("otp", "").strip()

        try:
            OTPService.verify_otp(
                target=new_target,
                channel=channel,
                purpose=OTPVerification.PURPOSE_CONTACT_CHANGE,
                plain_otp=otp,
            )
        except DjangoValidationError as err:
            raise serializers.ValidationError({"otp": str(err.message if hasattr(err, "message") else err)}) from err

        return attrs


class OTPRequestSerializer(serializers.Serializer):
    """Request generation and delivery of an OTP."""

    target = serializers.CharField(help_text="Target email or mobile number")
    channel = serializers.ChoiceField(choices=OTPVerification.CHANNEL_CHOICES)
    purpose = serializers.ChoiceField(
        choices=[
            OTPVerification.PURPOSE_REGISTRATION,
            OTPVerification.PURPOSE_LOGIN,
            OTPVerification.PURPOSE_ADMIN_MFA,
            OTPVerification.PURPOSE_PASSWORD_RESET,
            OTPVerification.PURPOSE_CONTACT_CHANGE,
        ],
        default=OTPVerification.PURPOSE_LOGIN,
    )


class OTPVerifySerializer(serializers.Serializer):
    """Verify an issued OTP token."""

    target = serializers.CharField()
    channel = serializers.ChoiceField(choices=OTPVerification.CHANNEL_CHOICES)
    purpose = serializers.ChoiceField(
        choices=[
            OTPVerification.PURPOSE_REGISTRATION,
            OTPVerification.PURPOSE_LOGIN,
            OTPVerification.PURPOSE_ADMIN_MFA,
            OTPVerification.PURPOSE_PASSWORD_RESET,
            OTPVerification.PURPOSE_CONTACT_CHANGE,
        ],
    )
    otp = serializers.CharField(min_length=6, max_length=6)


class OTPLoginSerializer(serializers.Serializer):
    """Passwordless login using either verified email or verified mobile number + OTP."""

    target = serializers.CharField(help_text="Registered email address or phone number")
    channel = serializers.ChoiceField(choices=OTPVerification.CHANNEL_CHOICES)
    otp = serializers.CharField(min_length=6, max_length=6)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        target = attrs.get("target", "").strip()
        channel = attrs.get("channel")
        otp = attrs.get("otp", "").strip()

        user = None
        if channel == OTPVerification.CHANNEL_EMAIL:
            user = User.objects.filter(email__iexact=target).first()
            if not user:
                raise serializers.ValidationError({"target": "No user registered with this email address."})
            if not user.is_email_verified:
                raise serializers.ValidationError(
                    {"target": "This email has not been verified yet. Complete registration verification first."}
                )
        elif channel == OTPVerification.CHANNEL_SMS:
            user = User.objects.filter(phone=target).first()
            if not user:
                raise serializers.ValidationError({"target": "No user registered with this phone number."})
            if not user.is_mobile_verified:
                raise serializers.ValidationError(
                    {"target": "This mobile number has not been verified yet. Complete registration verification first."}
                )

        if not user.is_active:
            raise serializers.ValidationError({"detail": "This user account is inactive."})

        OTPService.verify_otp(
            target=target,
            channel=channel,
            purpose=OTPVerification.PURPOSE_LOGIN,
            plain_otp=otp,
        )

        attrs["user"] = user
        return attrs


class AdminInvitationCreateSerializer(serializers.ModelSerializer):
    """Create an admin account invitation."""

    role_code = serializers.ChoiceField(choices=[Role.SOCIETY_ADMIN, Role.PLATFORM_ADMIN])

    class Meta:
        model = AdminInvitation
        fields = ["email", "role_code"]

    def validate_email(self, value: str) -> str:
        lowered = value.strip().lower()
        if User.objects.filter(email=lowered).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return lowered


class AdminInvitationAcceptSerializer(serializers.Serializer):
    """Accept invitation and activate administrator credentials."""

    token = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=10)
    first_name = serializers.CharField(required=False, default="")
    last_name = serializers.CharField(required=False, default="")
    phone = serializers.CharField(required=False, default="")
    mfa_enabled = serializers.BooleanField(default=True)


class TokenResponseSerializer(serializers.Serializer):
    """JWT Token pair response."""

    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()
