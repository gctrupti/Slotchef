"""URL routes for Identity domain."""

from __future__ import annotations

from django.urls import path

from apps.identity.views import (
    AdminAcceptInvitationView,
    AdminInviteView,
    AdminMFAVerifyView,
    ContactChangeConfirmView,
    ContactChangeRequestView,
    LoginView,
    LogoutView,
    MeView,
    OTPLoginView,
    OTPRequestView,
    OTPVerifyView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RegisterVerifyOTPView,
    RegisterView,
)

urlpatterns = [
    # Registration Flow (Step 1: Initiate, Step 2: Verify OTP)
    path("auth/register", RegisterView.as_view(), name="auth-register"),
    path("auth/register/verify-otp", RegisterVerifyOTPView.as_view(), name="auth-register-verify-otp"),

    # Password Login with Email or Mobile Number (Brute-force protected)
    path("auth/login", LoginView.as_view(), name="auth-login"),
    path("auth/admin/mfa-verify", AdminMFAVerifyView.as_view(), name="auth-admin-mfa-verify"),

    # Forgot Password Flow (OTP verification)
    path("auth/password-reset/request", PasswordResetRequestView.as_view(), name="auth-password-reset-request"),
    path("auth/password-reset/confirm", PasswordResetConfirmView.as_view(), name="auth-password-reset-confirm"),

    # Contact Change Flow (with OTP verification on new target)
    path("auth/contact/request-change", ContactChangeRequestView.as_view(), name="auth-contact-request-change"),
    path("auth/contact/confirm-change", ContactChangeConfirmView.as_view(), name="auth-contact-confirm-change"),

    # Reusable OTP Request, Verify, & Passwordless endpoints
    path("auth/otp/request", OTPRequestView.as_view(), name="auth-otp-request"),
    path("auth/otp/verify", OTPVerifyView.as_view(), name="auth-otp-verify"),
    path("auth/otp/login", OTPLoginView.as_view(), name="auth-otp-login"),
    path("auth/logout", LogoutView.as_view(), name="auth-logout"),

    # Admin Invitation Workflow
    path("auth/admin/invite", AdminInviteView.as_view(), name="auth-admin-invite"),
    path("auth/admin/accept-invitation", AdminAcceptInvitationView.as_view(), name="auth-admin-accept-invitation"),

    # Profile & RBAC Context
    path("me", MeView.as_view(), name="user-me"),
]
