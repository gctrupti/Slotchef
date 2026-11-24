"""Authentication and user context views supporting unified OTP and 3-portal RBAC."""

from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.audit.models import AuditLog
from apps.identity.models import AdminInvitation, OTPVerification, Role, User, UserRole
from apps.identity.serializers import (
    AdminInvitationAcceptSerializer,
    AdminInvitationCreateSerializer,
    AdminMFAVerifySerializer,
    ContactChangeConfirmSerializer,
    ContactChangeRequestSerializer,
    LoginSerializer,
    OTPLoginSerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    RegisterVerifyOTPSerializer,
    TokenResponseSerializer,
    UserSerializer,
)
from apps.identity.services.otp_service import OTPService


class RegisterView(APIView):
    """Step 1: Register a new user account (strictly household_member or cook) with initial channel OTP dispatch."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=RegisterSerializer,
        responses={201: dict},
        summary="Register user account (Cook or Household) - Step 1",
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        channel = getattr(user, "_selected_verification_channel", "email")
        target = getattr(user, "_verification_target", user.email)

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "verification_channel": channel,
                "verification_target": target,
                "message": f"Registration initiated. Verification OTP sent to {channel} ({target}). Please verify OTP to activate.",
            },
            status=status.HTTP_201_CREATED,
        )


class RegisterVerifyOTPView(APIView):
    """Step 2: Verify registration OTP code to confirm contact channel and activate credentials."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=RegisterVerifyOTPSerializer,
        responses={200: TokenResponseSerializer},
        summary="Verify Registration OTP - Step 2",
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = RegisterVerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "message": "Contact verified successfully. You may now proceed or verify your secondary contact.",
            },
            status=status.HTTP_200_OK,
        )


class LoginView(APIView):
    """Authenticate with registered mobile number OR registered email and password (no OTP for normal users)."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=LoginSerializer,
        responses={200: TokenResponseSerializer},
        summary="Login with Email or Mobile Number + Password",
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        # If Admin MFA is required, return challenge token instead of direct JWT access
        if serializer.validated_data.get("mfa_required"):
            challenge = serializer.validated_data["mfa_challenge"]
            return Response(challenge, status=status.HTTP_200_OK)

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )


class AdminMFAVerifyView(APIView):
    """Verify administrator MFA step-up code to receive full access JWT tokens."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=AdminMFAVerifySerializer,
        responses={200: TokenResponseSerializer},
        summary="Complete Admin MFA Step-up Authentication",
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = AdminMFAVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetRequestView(APIView):
    """Request a password reset OTP for registered mobile or email."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=PasswordResetRequestSerializer,
        responses={200: dict},
        summary="Request Password Reset OTP",
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target = serializer.validated_data["target"]
        channel = serializer.validated_data["channel"]
        user = serializer.validated_data["user"]

        try:
            OTPService.request_otp(
                target=target,
                channel=channel,
                purpose=OTPVerification.PURPOSE_PASSWORD_RESET,
                user=user,
            )
        except ValidationError as err:
            return Response({"detail": str(err.message if hasattr(err, "message") else err)}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        return Response(
            {"detail": f"Password reset OTP sent to {channel} channel.", "cooldown_seconds": 60},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    """Confirm password reset with OTP verification."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=PasswordResetConfirmSerializer,
        responses={200: dict},
        summary="Confirm Password Reset with OTP",
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        new_password = serializer.validated_data["new_password"]

        with transaction.atomic():
            user.set_password(new_password)
            user.save()

            AuditLog.objects.create(
                actor=user,
                action="auth.password_reset_completed",
                entity_type="User",
                entity_id=str(user.id),
                after_state={"email": user.email},
            )

        return Response({"detail": "Password has been successfully reset. You may now log in with your new password."}, status=status.HTTP_200_OK)


class ContactChangeRequestView(APIView):
    """Request updating contact email or phone requiring OTP verification on the new target."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=ContactChangeRequestSerializer,
        responses={200: dict},
        summary="Request Contact Change OTP",
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = ContactChangeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_target = serializer.validated_data["new_target"]
        channel = serializer.validated_data["channel"]

        try:
            OTPService.request_otp(
                target=new_target,
                channel=channel,
                purpose=OTPVerification.PURPOSE_CONTACT_CHANGE,
                user=request.user,
            )
        except ValidationError as err:
            return Response({"detail": str(err.message if hasattr(err, "message") else err)}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        return Response(
            {"detail": f"Verification OTP sent to new {channel} target {new_target}.", "cooldown_seconds": 60},
            status=status.HTTP_200_OK,
        )


class ContactChangeConfirmView(APIView):
    """Confirm updating contact email or phone with verified OTP on the new target."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=ContactChangeConfirmSerializer,
        responses={200: UserSerializer},
        summary="Confirm Contact Change with OTP",
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = ContactChangeConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_target = serializer.validated_data["new_target"]
        channel = serializer.validated_data["channel"]
        user = request.user

        with transaction.atomic():
            if channel == OTPVerification.CHANNEL_EMAIL:
                old_contact = user.email
                user.email = new_target
                user.is_email_verified = True
            else:
                old_contact = user.phone
                user.phone = new_target
                user.is_mobile_verified = True

            user.save()

            AuditLog.objects.create(
                actor=user,
                action="auth.contact_updated",
                entity_type="User",
                entity_id=str(user.id),
                after_state={
                    "channel": channel,
                    "old_contact": old_contact,
                    "new_contact": new_target,
                },
            )

        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


class OTPRequestView(APIView):
    """Request an OTP for registration, login, or MFA."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=OTPRequestSerializer,
        responses={200: dict},
        summary="Request OTP code via SMS or Email",
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = OTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target = serializer.validated_data["target"]
        channel = serializer.validated_data["channel"]
        purpose = serializer.validated_data["purpose"]

        try:
            OTPService.request_otp(target=target, channel=channel, purpose=purpose)
        except ValidationError as err:
            return Response({"detail": str(err.message if hasattr(err, "message") else err)}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        return Response(
            {"detail": f"OTP sent successfully to {channel} channel.", "cooldown_seconds": 60},
            status=status.HTTP_200_OK,
        )


class OTPVerifyView(APIView):
    """Verify an issued OTP code to complete channel verification."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=OTPVerifySerializer,
        responses={200: dict},
        summary="Verify OTP code",
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target = serializer.validated_data["target"]
        channel = serializer.validated_data["channel"]
        purpose = serializer.validated_data["purpose"]
        otp = serializer.validated_data["otp"]

        try:
            OTPService.verify_otp(target=target, channel=channel, purpose=purpose, plain_otp=otp)
        except ValidationError as err:
            return Response({"detail": str(err.message if hasattr(err, "message") else err)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": f"{channel.title()} channel verified successfully."}, status=status.HTTP_200_OK)


class OTPLoginView(APIView):
    """Optional passwordless login using either verified mobile number or verified email + OTP."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=OTPLoginSerializer,
        responses={200: TokenResponseSerializer},
        summary="Login with OTP code",
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = OTPLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """Revoke user JWT refresh token upon sign out."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=dict,
        responses={200: dict},
        summary="Revoke JWT tokens on logout",
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        refresh_token = request.data.get("refresh")
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:
                pass
        return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)


class AdminInviteView(APIView):
    """Invite an administrator to join with society_admin or platform_admin role."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=AdminInvitationCreateSerializer,
        responses={201: dict},
        summary="Create Admin Invitation (Platform Admin only)",
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        if not (request.user.is_superuser or request.user.has_role(Role.PLATFORM_ADMIN)):
            return Response({"detail": "Forbidden: Only Platform Admins can invite new administrators."}, status=status.HTTP_403_FORBIDDEN)

        serializer = AdminInvitationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].strip().lower()
        role_code = serializer.validated_data["role_code"]
        role = get_object_or_404(Role, code=role_code)

        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

        invitation, _ = AdminInvitation.objects.update_or_create(
            email=email,
            defaults={
                "role": role,
                "invited_by": request.user,
                "token_hash": token_hash,
                "status": AdminInvitation.STATUS_PENDING,
                "expires_at": timezone.now() + timedelta(days=3),
            },
        )

        AuditLog.objects.create(
            actor=request.user,
            action="admin.invitation_created",
            entity_type="AdminInvitation",
            entity_id=str(invitation.id),
            after_state={"email": email, "role": role.code},
        )

        return Response(
            {
                "invitation_id": str(invitation.id),
                "email": invitation.email,
                "role": role.code,
                "invitation_token": raw_token,
                "expires_at": invitation.expires_at.isoformat(),
            },
            status=status.HTTP_201_CREATED,
        )


class AdminAcceptInvitationView(APIView):
    """Accept an administrator invitation and activate credentials."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=AdminInvitationAcceptSerializer,
        responses={200: TokenResponseSerializer},
        summary="Accept Admin Invitation and set credentials",
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = AdminInvitationAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"].strip()
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

        invitation = AdminInvitation.objects.filter(
            token_hash=token_hash,
            status=AdminInvitation.STATUS_PENDING,
            expires_at__gt=timezone.now(),
        ).first()

        if not invitation:
            return Response({"detail": "Invalid or expired invitation token."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            user = User.objects.create_user(
                email=invitation.email,
                password=serializer.validated_data["password"],
                first_name=serializer.validated_data.get("first_name", ""),
                last_name=serializer.validated_data.get("last_name", ""),
                phone=serializer.validated_data.get("phone", ""),
                is_email_verified=True,
                is_mobile_verified=True,
                mfa_enabled=serializer.validated_data.get("mfa_enabled", True),
                is_staff=True,
            )

            UserRole.objects.create(user=user, role=invitation.role)
            invitation.status = AdminInvitation.STATUS_ACCEPTED
            invitation.save(update_fields=["status"])

            AuditLog.objects.create(
                actor=user,
                action="admin.invitation_accepted",
                entity_type="AdminInvitation",
                entity_id=str(invitation.id),
                after_state={"user_id": str(user.id), "role": invitation.role.code},
            )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    """Retrieve details, roles, and profile context of the authenticated user."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={200: UserSerializer},
        summary="Current user profile and memberships",
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = request.user
        data = UserSerializer(user).data

        if hasattr(user, "cook_profile"):
            cp = user.cook_profile
            data["cook_profile"] = {
                "id": str(cp.id),
                "verification_status": cp.verification_status,
                "active_status": cp.active_status,
                "max_daily_minutes": cp.max_daily_minutes,
                "max_daily_visits": cp.max_daily_visits,
            }

        memberships = user.household_memberships.filter(is_active=True).select_related(
            "household__society"
        )
        data["households"] = [
            {
                "id": str(m.household_id),
                "society_id": str(m.household.society_id),
                "society_name": m.household.society.name,
                "apartment_label": m.household.apartment_label,
                "role": m.role,
            }
            for m in memberships
        ]

        return Response(data, status=status.HTTP_200_OK)
