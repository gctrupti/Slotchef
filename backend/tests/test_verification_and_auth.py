"""Test suite for Phase 11: Identity verification, OTP authentication, and Admin onboarding."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.communities.models import Building, Society
from apps.cooks.models import CookProfile, CookVerificationProfile
from apps.households.models import Household, HouseholdMember, HouseholdVerificationProfile
from apps.identity.models import OTPVerification, Role
from apps.identity.providers.email_provider import MockEmailProvider
from apps.identity.providers.sms_provider import MockSMSProvider
from apps.identity.services.otp_service import OTPService

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def superuser():
    return User.objects.create_superuser(
        email="superadmin@slotchef.test",
        password="SuperAdminPassword123!",
        first_name="Super",
        last_name="Admin",
    )


@pytest.fixture
def society():
    return Society.objects.create(name="Godrej Woods", address="Sector 43, Noida")


@pytest.fixture
def building(society):
    return Building.objects.create(society=society, name="Tower Aster")


@pytest.mark.django_db
def test_public_registration_blocks_administrative_roles(api_client):
    """Public registration must reject requests attempting to create admin accounts."""
    payload = {
        "email": "hacker@evil.test",
        "password": "Password123!",
        "phone": "+919876543210",
        "role": Role.PLATFORM_ADMIN,
    }
    response = api_client.post("/api/v1/auth/register", data=payload)
    assert response.status_code == 400
    details = response.data.get("error", {}).get("details", response.data)
    assert "role" in details or "detail" in response.data


@pytest.mark.django_db
def test_registration_triggers_dual_channel_otp(api_client):
    """Registration creates user in unverified status and dispatches OTPs."""
    MockSMSProvider.sent_messages.clear()
    MockEmailProvider.sent_emails.clear()

    payload = {
        "email": "resident1@godrej.test",
        "password": "ValidPassword123!",
        "phone": "+919876543211",
        "role": Role.HOUSEHOLD_MEMBER,
        "first_name": "Rohan",
        "last_name": "Sharma",
    }
    response = api_client.post("/api/v1/auth/register", data=payload)
    assert response.status_code == 201

    user = User.objects.get(email="resident1@godrej.test")
    assert not user.is_email_verified
    assert not user.is_mobile_verified
    assert not user.is_fully_verified

    # Verify initial selected channel OTP dispatched
    sms_otps = OTPVerification.objects.filter(target="+919876543211", channel="sms")
    assert sms_otps.exists()

    # Request sequential verification OTP for second channel (email)
    OTPService.request_otp(
        target="resident1@godrej.test",
        channel="email",
        purpose=OTPVerification.PURPOSE_REGISTRATION,
        user=user,
    )
    email_otps = OTPVerification.objects.filter(target="resident1@godrej.test", channel="email")
    assert email_otps.exists()


@pytest.mark.django_db
def test_otp_rate_limiting_and_max_attempts():
    """OTP service enforces cooldown rate limiting and invalidation on excessive attempts."""
    target = "+919999988888"
    verification, plain_otp = OTPService.request_otp(
        target=target,
        channel=OTPVerification.CHANNEL_SMS,
        purpose=OTPVerification.PURPOSE_LOGIN,
    )
    assert verification is not None

    # Immediate second request should fail cooldown
    with pytest.raises(ValidationError) as exc:
        OTPService.request_otp(
            target=target,
            channel=OTPVerification.CHANNEL_SMS,
            purpose=OTPVerification.PURPOSE_LOGIN,
        )
    assert "Rate limit exceeded" in str(exc.value)

    # Failed attempts
    with pytest.raises(ValidationError) as exc1:
        OTPService.verify_otp(target, OTPVerification.CHANNEL_SMS, OTPVerification.PURPOSE_LOGIN, "000000")
    assert "2 attempts remaining" in str(exc1.value)

    with pytest.raises(ValidationError):
        OTPService.verify_otp(target, OTPVerification.CHANNEL_SMS, OTPVerification.PURPOSE_LOGIN, "000001")

    with pytest.raises(ValidationError) as exc3:
        OTPService.verify_otp(target, OTPVerification.CHANNEL_SMS, OTPVerification.PURPOSE_LOGIN, "000002")
    assert "Maximum attempts exceeded" in str(exc3.value)

    # Next attempt should report no active request
    with pytest.raises(ValidationError) as exc4:
        OTPService.verify_otp(target, OTPVerification.CHANNEL_SMS, OTPVerification.PURPOSE_LOGIN, plain_otp)
    assert "No active OTP request" in str(exc4.value)


@pytest.mark.django_db
def test_otp_login_single_channel_workflow(api_client):
    """User can log in using either verified mobile or verified email with valid OTP."""
    user = User.objects.create_user(
        email="verifieduser@slotchef.test",
        password="SomePassword123!",
        phone="+919111122222",
        is_email_verified=True,
        is_mobile_verified=True,
    )

    # Request OTP for email
    req_resp = api_client.post(
        "/api/v1/auth/otp/request",
        data={"target": user.email, "channel": "email", "purpose": "login"},
    )
    assert req_resp.status_code == 200

    OTPVerification.objects.filter(target=user.email, purpose="login").first()
    # Find plaintext OTP from mock provider
    sent = MockEmailProvider.sent_emails[-1]
    plain_otp = sent["otp"]

    login_resp = api_client.post(
        "/api/v1/auth/otp/login",
        data={"target": user.email, "channel": "email", "otp": plain_otp},
    )
    assert login_resp.status_code == 200
    assert "access" in login_resp.data
    assert "refresh" in login_resp.data
    assert login_resp.data["user"]["email"] == user.email


@pytest.mark.django_db
def test_admin_invitation_lifecycle(api_client, superuser):
    """Platform admin invites society admin, who accepts with credentials."""
    api_client.force_authenticate(user=superuser)

    # Ensure society_admin role exists
    Role.objects.get_or_create(code=Role.SOCIETY_ADMIN, defaults={"name": "Society Administrator"})

    invite_resp = api_client.post(
        "/api/v1/auth/admin/invite",
        data={"email": "societyadmin@godrej.test", "role_code": Role.SOCIETY_ADMIN},
    )
    assert invite_resp.status_code == 201
    raw_token = invite_resp.data["invitation_token"]

    # Log out
    api_client.force_authenticate(user=None)

    # Accept invitation
    accept_resp = api_client.post(
        "/api/v1/auth/admin/accept-invitation",
        data={
            "token": raw_token,
            "password": "StrongAdminPassword123!",
            "first_name": "Anil",
            "last_name": "Kapoor",
            "phone": "+919876500000",
        },
    )
    assert accept_resp.status_code == 200
    assert "access" in accept_resp.data

    admin_user = User.objects.get(email="societyadmin@godrej.test")
    assert admin_user.is_staff
    assert admin_user.has_role(Role.SOCIETY_ADMIN)


@pytest.mark.django_db
def test_cook_verification_and_admin_approval(api_client, superuser):
    """Cook submits documents & experience, admin verifies and activates cook."""
    cook_user = User.objects.create_user(
        email="masterchef@slotchef.test",
        password="Password123!",
        phone="+919555544444",
        is_email_verified=True,
        is_mobile_verified=True,
    )
    cook_profile = CookProfile.objects.create(
        user=cook_user,
        verification_status=CookProfile.VERIFICATION_PENDING,
    )

    api_client.force_authenticate(user=cook_user)

    # Submit verification dossier
    submit_resp = api_client.post(
        "/api/v1/cooks/me/verification",
        data={
            "document_type": CookVerificationProfile.DOC_AADHAAR,
            "masked_document_number": "XXXXXXXX9876",
            "document_reference": "vault://docs/aadhaar_9876.enc",
            "years_of_experience": 8,
            "reference_contact_name": "Chef Sanjeev",
            "reference_contact_phone": "+919820011223",
        },
    )
    assert submit_resp.status_code == 200
    assert submit_resp.data["background_verification_status"] == "clear"

    # Admin reviews and approves
    api_client.force_authenticate(user=superuser)
    review_resp = api_client.post(
        f"/api/v1/admin/cooks/{cook_profile.id}/verification",
        data={
            "status": CookVerificationProfile.STATUS_VERIFIED,
            "reference_verified": True,
            "admin_notes": "Background clear, 8 years commercial experience confirmed.",
        },
    )
    assert review_resp.status_code == 200
    assert review_resp.data["status"] == "verified"

    cook_profile.refresh_from_db()
    assert cook_profile.verification_status == CookProfile.VERIFICATION_VERIFIED
    assert cook_profile.is_eligible_to_work


@pytest.mark.django_db
def test_household_residency_verification(api_client, superuser, building):
    """Household submits residency document and admin approves."""
    resident_user = User.objects.create_user(
        email="owner@apartment.test",
        password="Password123!",
        is_email_verified=True,
        is_mobile_verified=True,
    )
    household = Household.objects.create(
        society=building.society,
        building=building,
        apartment_label="Flat 1402",
    )
    HouseholdMember.objects.create(
        household=household,
        user=resident_user,
        role=HouseholdMember.ROLE_PRIMARY,
    )

    api_client.force_authenticate(user=resident_user)

    # Submit residency proof
    submit_resp = api_client.post(
        f"/api/v1/households/{household.id}/verification",
        data={
            "residency_type": HouseholdVerificationProfile.RESIDENCY_OWNER,
            "possession_proof_type": HouseholdVerificationProfile.PROOF_UTILITY_BILL,
            "possession_proof_reference": "vault://bills/oct2026_elec.pdf",
        },
    )
    assert submit_resp.status_code == 200
    assert submit_resp.data["status"] == "in_review"

    # Admin approves
    api_client.force_authenticate(user=superuser)
    review_resp = api_client.post(
        f"/api/v1/admin/households/{household.id}/verification",
        data={
            "status": HouseholdVerificationProfile.STATUS_VERIFIED,
            "society_noc_verified": True,
            "admin_notes": "Flat ownership cross-checked with Godrej society registry.",
        },
    )
    assert review_resp.status_code == 200
    assert review_resp.data["status"] == "verified"
    assert review_resp.data["society_noc_verified"] is True
