"""Test suite for Authentication Decision: Registration OTP, Password Login, Brute-force protection, Forgot Password, Contact Change, and Admin MFA."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.communities.models import Building, Society
from apps.households.models import Household, HouseholdMember, HouseholdVerificationProfile
from apps.identity.models import Role
from apps.identity.providers.email_provider import MockEmailProvider
from apps.identity.providers.sms_provider import MockSMSProvider

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def superuser():
    return User.objects.create_superuser(
        email="rootadmin@slotchef.test",
        password="SuperAdminPassword123!",
        first_name="Root",
        last_name="Administrator",
    )


@pytest.fixture
def society():
    return Society.objects.create(name="Prestige Lakeside Habitat", address="Varthur, Bangalore")


@pytest.fixture
def building(society):
    return Building.objects.create(society=society, name="Tower 5")


@pytest.fixture
def household(building):
    return Household.objects.create(
        society=building.society,
        building=building,
        apartment_label="Flat 304",
    )


@pytest.mark.django_db
def test_registration_with_selected_channel_and_otp_verification(api_client):
    """Step 1 & Step 2: Register with mobile/email, receive OTP on chosen channel, verify OTP to complete registration."""
    MockSMSProvider.sent_messages.clear()

    # Step 1: Initiate registration selecting SMS channel
    reg_payload = {
        "first_name": "Aarav",
        "last_name": "Patel",
        "email": "aarav.patel@test.com",
        "phone": "+919812345678",
        "password": "StrongPassword123!",
        "role": Role.HOUSEHOLD_MEMBER,
        "verification_channel": "sms",
    }
    resp1 = api_client.post("/api/v1/auth/register", data=reg_payload)
    assert resp1.status_code == 201
    assert resp1.data["verification_channel"] == "sms"

    user = User.objects.get(email="aarav.patel@test.com")
    assert not user.is_mobile_verified
    assert not user.is_email_verified
    assert not user.is_fully_verified

    # Step 2: Verify OTP delivered to mobile
    assert len(MockSMSProvider.sent_messages) >= 1
    otp_code = MockSMSProvider.sent_messages[-1]["otp"]

    verify_payload = {
        "target": "+919812345678",
        "channel": "sms",
        "otp": otp_code,
    }
    resp2 = api_client.post("/api/v1/auth/register/verify-otp", data=verify_payload)
    assert resp2.status_code == 200
    assert "access" in resp2.data
    assert "refresh" in resp2.data

    user.refresh_from_db()
    assert user.is_mobile_verified is True
    assert user.is_email_verified is False
    assert user.is_fully_verified is False


@pytest.mark.django_db
def test_sequential_second_channel_verification(api_client):
    """Step 3: Sequentially verify remaining channel to achieve full verification."""
    MockEmailProvider.sent_emails.clear()

    user = User.objects.create_user(
        email="sequential@slotchef.test",
        password="Password123!",
        phone="+919876543219",
        is_mobile_verified=True,
        is_email_verified=False,
    )
    api_client.force_authenticate(user=user)

    # Request OTP for second channel (email)
    req_resp = api_client.post(
        "/api/v1/auth/otp/request",
        data={"target": user.email, "channel": "email", "purpose": "registration"},
    )
    assert req_resp.status_code == 200

    assert len(MockEmailProvider.sent_emails) >= 1
    email_otp = MockEmailProvider.sent_emails[-1]["otp"]

    # Verify second channel
    ver_resp = api_client.post(
        "/api/v1/auth/otp/verify",
        data={"target": user.email, "channel": "email", "purpose": "registration", "otp": email_otp},
    )
    assert ver_resp.status_code == 200

    user.refresh_from_db()
    assert user.is_email_verified is True
    assert user.is_mobile_verified is True
    assert user.is_fully_verified is True


@pytest.mark.django_db
def test_normal_login_with_email_and_password_no_otp_required(api_client):
    """Existing user logs in directly using email + password without mandatory OTP."""
    user = User.objects.create_user(
        email="emailuser@slotchef.test",
        password="ValidPassword123!",
        phone="+919999911111",
        is_email_verified=True,
    )

    login_resp = api_client.post(
        "/api/v1/auth/login",
        data={"identifier": "emailuser@slotchef.test", "password": "ValidPassword123!"},
    )
    assert login_resp.status_code == 200
    assert "access" in login_resp.data
    assert "refresh" in login_resp.data
    assert login_resp.data["user"]["email"] == user.email


@pytest.mark.django_db
def test_normal_login_with_phone_and_password_no_otp_required(api_client):
    """Existing user logs in directly using registered mobile number + password without mandatory OTP."""
    user = User.objects.create_user(
        email="phoneuser@slotchef.test",
        password="ValidPassword123!",
        phone="+919999922222",
        is_mobile_verified=True,
    )

    login_resp = api_client.post(
        "/api/v1/auth/login",
        data={"identifier": "+919999922222", "password": "ValidPassword123!"},
    )
    assert login_resp.status_code == 200
    assert "access" in login_resp.data
    assert "refresh" in login_resp.data
    assert login_resp.data["user"]["email"] == user.email


@pytest.mark.django_db
def test_brute_force_lockout_after_five_failed_attempts(api_client):
    """Brute force defense: 5 consecutive failed login attempts trigger a 15-minute lockout."""
    User.objects.create_user(
        email="victim@slotchef.test",
        password="RealPassword123!",
        phone="+919999933333",
    )

    # 4 bad attempts
    for _ in range(4):
        resp = api_client.post(
            "/api/v1/auth/login",
            data={"identifier": "victim@slotchef.test", "password": "WrongPassword!"},
        )
        assert resp.status_code == 400
        assert "attempt(s) remaining" in str(resp.data)

    # 5th bad attempt -> locks account
    lock_resp = api_client.post(
        "/api/v1/auth/login",
        data={"identifier": "victim@slotchef.test", "password": "WrongPassword!"},
    )
    assert lock_resp.status_code == 400
    assert "locked for 15 minutes" in str(lock_resp.data)

    # Even with correct password, login is blocked while locked out
    blocked_resp = api_client.post(
        "/api/v1/auth/login",
        data={"identifier": "victim@slotchef.test", "password": "RealPassword123!"},
    )
    assert blocked_resp.status_code == 400
    assert "temporarily locked" in str(blocked_resp.data)


@pytest.mark.django_db
def test_admin_mfa_step_up_workflow(api_client, superuser):
    """Admin login requires password + stronger MFA step-up OTP verification."""
    MockEmailProvider.sent_emails.clear()

    # Create admin via invitation
    api_client.force_authenticate(user=superuser)
    Role.objects.get_or_create(code=Role.PLATFORM_ADMIN, defaults={"name": "Platform Administrator"})

    invite_resp = api_client.post(
        "/api/v1/auth/admin/invite",
        data={"email": "secadmin@slotchef.test", "role_code": Role.PLATFORM_ADMIN},
    )
    token = invite_resp.data["invitation_token"]

    api_client.force_authenticate(user=None)
    api_client.post(
        "/api/v1/auth/admin/accept-invitation",
        data={"token": token, "password": "AdminPassword123!", "mfa_enabled": True},
    )

    # 1. Admin logs in with password -> MFA challenge returned
    login_resp = api_client.post(
        "/api/v1/auth/login",
        data={"identifier": "secadmin@slotchef.test", "password": "AdminPassword123!"},
    )
    assert login_resp.status_code == 200
    assert login_resp.data["mfa_required"] is True
    mfa_session_token = login_resp.data["mfa_token"]

    # 2. MFA OTP delivered to admin email
    assert len(MockEmailProvider.sent_emails) >= 1
    mfa_otp = MockEmailProvider.sent_emails[-1]["otp"]

    # 3. Complete MFA verify
    mfa_resp = api_client.post(
        "/api/v1/auth/admin/mfa-verify",
        data={"mfa_token": mfa_session_token, "otp": mfa_otp},
    )
    assert mfa_resp.status_code == 200
    assert "access" in mfa_resp.data
    assert mfa_resp.data["user"]["email"] == "secadmin@slotchef.test"


@pytest.mark.django_db
def test_forgot_password_otp_reset_flow(api_client):
    """Forgot-password workflow verifies OTP and updates password securely."""
    MockEmailProvider.sent_emails.clear()

    User.objects.create_user(
        email="forgetful@slotchef.test",
        password="OldPassword123!",
        is_email_verified=True,
    )

    # 1. Request password reset OTP
    req_resp = api_client.post(
        "/api/v1/auth/password-reset/request",
        data={"target": "forgetful@slotchef.test", "channel": "email"},
    )
    assert req_resp.status_code == 200

    assert len(MockEmailProvider.sent_emails) >= 1
    reset_otp = MockEmailProvider.sent_emails[-1]["otp"]

    # 2. Confirm password reset with new password
    confirm_resp = api_client.post(
        "/api/v1/auth/password-reset/confirm",
        data={
            "target": "forgetful@slotchef.test",
            "channel": "email",
            "otp": reset_otp,
            "new_password": "BrandNewPassword123!",
        },
    )
    assert confirm_resp.status_code == 200

    # 3. Log in with new password
    login_resp = api_client.post(
        "/api/v1/auth/login",
        data={"identifier": "forgetful@slotchef.test", "password": "BrandNewPassword123!"},
    )
    assert login_resp.status_code == 200
    assert "access" in login_resp.data


@pytest.mark.django_db
def test_contact_change_requires_otp_verification(api_client):
    """Changing mobile number or email requires OTP verification on the new contact target."""
    MockSMSProvider.sent_messages.clear()

    user = User.objects.create_user(
        email="resident.phonechange@slotchef.test",
        password="Password123!",
        phone="+919800000001",
        is_mobile_verified=True,
    )
    api_client.force_authenticate(user=user)

    # 1. Request change to new mobile number
    req_resp = api_client.post(
        "/api/v1/auth/contact/request-change",
        data={"new_target": "+919800000002", "channel": "sms"},
    )
    assert req_resp.status_code == 200

    assert len(MockSMSProvider.sent_messages) >= 1
    change_otp = MockSMSProvider.sent_messages[-1]["otp"]

    # 2. Confirm change with verified OTP
    confirm_resp = api_client.post(
        "/api/v1/auth/contact/confirm-change",
        data={"new_target": "+919800000002", "channel": "sms", "otp": change_otp},
    )
    assert confirm_resp.status_code == 200
    assert confirm_resp.data["phone"] == "+919800000002"

    user.refresh_from_db()
    assert user.phone == "+919800000002"
    assert user.is_mobile_verified is True


@pytest.mark.django_db
def test_unapproved_household_blocked_from_booking(api_client, household, building):
    """Unapproved / rejected / suspended household is blocked from booking functionality."""
    user = User.objects.create_user(
        email="unapproved.resident@slotchef.test",
        password="Password123!",
        is_email_verified=True,
        is_mobile_verified=True,
    )
    HouseholdMember.objects.create(
        household=household,
        user=user,
        role=HouseholdMember.ROLE_PRIMARY,
    )

    # Reject household verification
    HouseholdVerificationProfile.objects.create(
        household=household,
        status=HouseholdVerificationProfile.STATUS_REJECTED,
        admin_notes="Invalid flat documentation",
    )

    api_client.force_authenticate(user=user)
    booking_resp = api_client.post(
        f"/api/v1/households/{household.id}/bookings",
        data={
            "service_date": "2026-11-20",
            "earliest_start_minute": 1080,
            "latest_finish_minute": 1140,
            "duration_minutes": 60,
            "meal_type": "dinner",
        },
    )
    assert booking_resp.status_code == 403
    assert "verification is rejected" in str(booking_resp.data)

