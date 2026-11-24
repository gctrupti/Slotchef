"""Test suite for Phase 12: Visit Safety, Overdue Detection, Emergency Contacts, and SOS India 112 system."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.bookings.models import Booking
from apps.communities.models import Building, Society
from apps.cooks.models import CookProfile
from apps.households.models import Household, HouseholdMember
from apps.scheduling.models import CookAssignment, SchedulePlan
from apps.visits.models import (
    EmergencyContact,
    VisitSafetyCheck,
)
from apps.visits.providers.notification_provider import MockNotificationProvider
from apps.visits.services.safety_service import SafetyService

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def superuser():
    return User.objects.create_superuser(
        email="safetyadmin@slotchef.test",
        password="AdminPassword123!",
        first_name="Safety",
        last_name="Director",
    )


@pytest.fixture
def society():
    return Society.objects.create(name="DLF The Aralias", address="Golf Course Road, Gurgaon")


@pytest.fixture
def building(society):
    return Building.objects.create(society=society, name="Tower 4")


@pytest.fixture
def household(building):
    return Household.objects.create(
        society=building.society,
        building=building,
        apartment_label="Apt 1201",
    )


@pytest.fixture
def resident_user(household):
    u = User.objects.create_user(
        email="resident.aralias@test.com",
        password="Password123!",
        phone="+919811122233",
        first_name="Vikram",
        last_name="Mehta",
        is_email_verified=True,
        is_mobile_verified=True,
    )
    HouseholdMember.objects.create(
        household=household,
        user=u,
        role=HouseholdMember.ROLE_PRIMARY,
    )
    return u


@pytest.fixture
def cook_user():
    return User.objects.create_user(
        email="chef.vikas@test.com",
        password="Password123!",
        phone="+919876599999",
        first_name="Vikas",
        last_name="Khanna",
        is_email_verified=True,
        is_mobile_verified=True,
    )


@pytest.fixture
def cook_profile(cook_user):
    return CookProfile.objects.create(
        user=cook_user,
        verification_status=CookProfile.VERIFICATION_VERIFIED,
    )


@pytest.fixture
def visit_assignment(society, household, cook_profile):
    service_date = date.today()
    plan = SchedulePlan.objects.create(
        society=society,
        service_date=service_date,
        version=1,
    )
    booking = Booking.objects.create(
        household=household,
        requested_by=cook_profile.user,
        service_date=service_date,
        earliest_start_minute=1080,
        latest_finish_minute=1140,
        duration_minutes=60,
        meal_type="dinner",
        status=Booking.STATUS_CONFIRMED,
    )
    start_dt = timezone.make_aware(datetime.combine(service_date, time(18, 0)))
    end_dt = timezone.make_aware(datetime.combine(service_date, time(19, 0)))

    return CookAssignment.objects.create(
        schedule_plan=plan,
        booking=booking,
        cook=cook_profile,
        start_minute=1080,
        end_minute=1140,
        start_at=start_dt,
        end_at=end_dt,
        status=CookAssignment.STATUS_CONFIRMED,
    )


@pytest.mark.django_db
def test_cook_checkin_checkout_and_household_arrival_confirmation(api_client, visit_assignment, cook_user, resident_user):
    """Full lifecycle: Cook checks in, resident confirms arrival, cook checks out."""
    # 1. Cook check-in with GPS
    api_client.force_authenticate(user=cook_user)
    checkin_resp = api_client.post(
        f"/api/v1/assignments/{visit_assignment.id}/check-in",
        data={"latitude": 28.4595, "longitude": 77.0266, "notes": "Arrived at tower lobby"},
    )
    assert checkin_resp.status_code == 200

    safety_check = VisitSafetyCheck.objects.get(assignment=visit_assignment)
    assert safety_check.check_in_at is not None
    assert safety_check.last_latitude == Decimal("28.459500")

    # 2. Resident confirms arrival inside residence
    api_client.force_authenticate(user=resident_user)
    confirm_resp = api_client.post(
        f"/api/v1/assignments/{visit_assignment.id}/confirm-arrival",
        data={"notes": "Cook is in the kitchen preparing ingredients"},
    )
    assert confirm_resp.status_code == 200

    safety_check.refresh_from_db()
    assert safety_check.arrival_confirmed_at is not None
    assert safety_check.arrival_confirmed_by == resident_user

    # 3. Cook checks out after meal preparation
    api_client.force_authenticate(user=cook_user)
    checkout_resp = api_client.post(
        f"/api/v1/assignments/{visit_assignment.id}/check-out",
        data={"latitude": 28.4596, "longitude": 77.0267, "notes": "Meal cooked, kitchen cleaned"},
    )
    assert checkout_resp.status_code == 200

    safety_check.refresh_from_db()
    assert safety_check.check_out_at is not None


@pytest.mark.django_db
def test_overdue_visit_detection(visit_assignment):
    """Detect visits that are overdue past scheduled start grace period without check-in."""
    # Simulate past start time
    past_time = timezone.now() - timedelta(minutes=45)
    visit_assignment.start_at = past_time
    visit_assignment.save(update_fields=["start_at"])

    overdue_assignments = SafetyService.detect_overdue_visits(check_in_grace_minutes=20)
    assert len(overdue_assignments) == 1
    assert overdue_assignments[0].id == visit_assignment.id

    safety_check = VisitSafetyCheck.objects.get(assignment=visit_assignment)
    assert safety_check.is_overdue is True
    assert "Cook has not checked in" in safety_check.overdue_reason


@pytest.mark.django_db
def test_emergency_contact_crud(api_client, resident_user):
    """User can manage trusted emergency contacts."""
    api_client.force_authenticate(user=resident_user)

    # Create primary emergency contact
    create_resp = api_client.post(
        "/api/v1/safety/emergency-contacts",
        data={
            "name": "Pooja Mehta",
            "phone": "+919811199999",
            "relationship": "Spouse",
            "is_primary": True,
        },
    )
    assert create_resp.status_code == 201
    contact_id = create_resp.data["id"]

    # List emergency contacts
    list_resp = api_client.get("/api/v1/safety/emergency-contacts")
    assert list_resp.status_code == 200
    results = list_resp.data.get("results", list_resp.data)
    assert len(results) == 1
    assert results[0]["name"] == "Pooja Mehta"

    # Delete contact
    del_resp = api_client.delete(f"/api/v1/safety/emergency-contacts/{contact_id}")
    assert del_resp.status_code == 204
    assert not EmergencyContact.objects.filter(pk=contact_id).exists()


@pytest.mark.django_db
def test_sos_incident_trigger_and_india_112_metadata(api_client, visit_assignment, resident_user):
    """SOS trigger dispatches alerts to emergency contacts and generates India 112 metadata."""
    MockNotificationProvider.dispatched_alerts.clear()

    # Register an emergency contact
    EmergencyContact.objects.create(
        user=resident_user,
        name="Emergency Brother",
        phone="+919800011122",
        relationship="Brother",
        is_primary=True,
    )

    api_client.force_authenticate(user=resident_user)
    sos_resp = api_client.post(
        f"/api/v1/assignments/{visit_assignment.id}/sos",
        data={
            "latitude": 28.4595,
            "longitude": 77.0266,
            "notes": "Medical emergency, sudden kitchen injury",
        },
    )
    assert sos_resp.status_code == 201
    sos_data = sos_resp.data
    assert sos_data["status"] == "triggered"
    assert sos_data["external_dispatch_confirmed"] is False

    # Check India 112 metadata packet
    m112 = sos_data["india_112_metadata"]
    assert m112["emergency_helpline"] == "112"
    assert m112["society_name"] == "DLF The Aralias"
    assert m112["apartment_unit"] == "Apt 1201"
    assert m112["cook_name"] == "Vikas Khanna"

    # Check that alerts were dispatched
    assert len(MockNotificationProvider.dispatched_alerts) >= 1
    emergency_sms = [a for a in MockNotificationProvider.dispatched_alerts if a["recipient_target"] == "+919800011122"]
    assert len(emergency_sms) == 1
    assert "Call 112" in emergency_sms[0]["message"]


@pytest.mark.django_db
def test_consent_location_ping(api_client, visit_assignment, cook_user):
    """Cook shares active GPS coordinate ping during in-progress visit."""
    api_client.force_authenticate(user=cook_user)

    ping_resp = api_client.post(
        f"/api/v1/assignments/{visit_assignment.id}/location-ping",
        data={"latitude": 28.459512, "longitude": 77.026634},
    )
    assert ping_resp.status_code == 200
    assert ping_resp.data["location_sharing_consented"] is True
    assert ping_resp.data["last_latitude"] == "28.459512"
    assert ping_resp.data["last_longitude"] == "77.026634"
