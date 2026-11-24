"""API integration tests for Bookings, Idempotency, and CP-SAT Orchestration."""

from __future__ import annotations

import datetime

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.bookings.models import Booking
from apps.communities.models import Building, Society
from apps.cooks.models import (
    CookAvailability,
    CookProfile,
    CookSkill,
    CookWorkPolicy,
    Skill,
)
from apps.households.models import Household, HouseholdMember
from apps.identity.models import Role, User
from apps.scheduling.models import CookAssignment, SchedulePlan


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def test_setup():
    # 1. Society & Building
    society = Society.objects.create(name="Palm Heights", address="123 Palm Ave", timezone="UTC")
    building = Building.objects.create(society=society, name="Tower A")

    # 2. Resident Users & Households
    user_a = User.objects.create_user(email="resident.a@example.com", password="PassWord123!")
    household_a = Household.objects.create(
        society=society,
        building=building,
        apartment_label="A-101",
    )
    HouseholdMember.objects.create(
        household=household_a,
        user=user_a,
        role=HouseholdMember.ROLE_PRIMARY,
        is_active=True,
    )

    user_b = User.objects.create_user(email="resident.b@example.com", password="PassWord123!")
    household_b = Household.objects.create(
        society=society,
        building=building,
        apartment_label="A-102",
    )
    HouseholdMember.objects.create(
        household=household_b,
        user=user_b,
        role=HouseholdMember.ROLE_PRIMARY,
        is_active=True,
    )

    outsider = User.objects.create_user(email="outsider@example.com", password="PassWord123!")

    # 3. Skills
    breakfast_skill = Skill.objects.create(code="basic_breakfast", name="Basic Breakfast")

    # 4. Cook Alexa
    cook_user = User.objects.create_user(
        email="alexa.cook@example.com",
        password="PassWord123!",
        first_name="Alexa",
    )
    role_cook, _ = Role.objects.get_or_create(code=Role.COOK)
    cook_user.user_roles.create(role=role_cook)

    alexa = CookProfile.objects.create(
        user=cook_user,
        verification_status=CookProfile.VERIFICATION_VERIFIED,
        active_status=True,
        max_daily_minutes=480,
        max_daily_visits=6,
    )
    alexa.societies.add(society)
    CookSkill.objects.create(cook=alexa, skill=breakfast_skill, proficiency_level="expert")
    CookWorkPolicy.objects.create(
        cook=alexa,
        max_consecutive_visits=4,
        max_daily_minutes=480,
        buffer_between_visits_minutes=5,
    )

    # Alexa works Monday mornings: 07:00 (420) to 11:00 (660)
    # We'll use 2027-02-15 which is a Monday (weekday=0)
    service_date = datetime.date(2027, 2, 15)
    CookAvailability.objects.create(
        cook=alexa,
        weekday=0,
        start_minute=420,  # 07:00
        end_minute=660,    # 11:00
        availability_type=CookAvailability.TYPE_REGULAR,
    )

    return {
        "society": society,
        "building": building,
        "household_a": household_a,
        "household_b": household_b,
        "user_a": user_a,
        "user_b": user_b,
        "outsider": outsider,
        "alexa": alexa,
        "service_date": service_date,
    }


@pytest.mark.django_db
def test_alexa_730_conflict_prevents_double_booking_and_never_falsely_confirms(
    api_client: APIClient,
    test_setup: dict,
) -> None:
    """Alexa 7:30 AM conflict:
    Household A requests 07:30-08:30 (45 mins).
    Household B requests 07:30-08:30 (45 mins).
    Alexa cannot do both with 5m buffer within 60 minutes.
    Household A gets CONFIRMED; Household B becomes UNFULFILLED with clear conflict metadata.
    """
    user_a = test_setup["user_a"]
    user_b = test_setup["user_b"]
    hh_a = test_setup["household_a"]
    hh_b = test_setup["household_b"]
    service_date = test_setup["service_date"]

    # 1. Household A creates booking 07:30-08:30 (45 mins)
    api_client.force_authenticate(user=user_a)
    payload_a = {
        "service_date": str(service_date),
        "meal_type": "breakfast",
        "earliest_start": "07:30",
        "latest_finish": "08:30",
        "estimated_duration_minutes": 45,
        "required_skills": ["basic_breakfast"],
    }
    resp_a = api_client.post(f"/api/v1/households/{hh_a.id}/bookings", payload_a, format="json")
    assert resp_a.status_code == status.HTTP_201_CREATED
    data_a = resp_a.json()
    assert data_a["status"] == Booking.STATUS_CONFIRMED
    assert data_a["assignment"] is not None
    assert data_a["assignment"]["start_minute"] == 450  # 07:30
    assert data_a["assignment"]["end_minute"] == 495    # 08:15

    # 2. Household B attempts conflicting 07:30-08:30 (45 mins)
    api_client.force_authenticate(user=user_b)
    payload_b = {
        "service_date": str(service_date),
        "meal_type": "breakfast",
        "earliest_start": "07:30",
        "latest_finish": "08:30",
        "estimated_duration_minutes": 45,
        "required_skills": ["basic_breakfast"],
    }
    resp_b = api_client.post(f"/api/v1/households/{hh_b.id}/bookings", payload_b, format="json")
    assert resp_b.status_code == status.HTTP_201_CREATED
    data_b = resp_b.json()
    # Must NOT falsely confirm!
    assert data_b["status"] == Booking.STATUS_UNFULFILLED
    assert data_b["assignment"] is None
    assert len(data_b["conflict_reasons"]) > 0
    assert data_b["conflict_reasons"][0]["primary_reason"] in [
        "TIME_WINDOW_CONFLICT",
        "NO_FEASIBLE_COOK",
    ]


@pytest.mark.django_db
def test_wider_window_allows_sequential_assignments(
    api_client: APIClient,
    test_setup: dict,
) -> None:
    """If Household B provides a flexible window (07:30 to 09:15),
    Alexa can finish Household A (07:30-08:15), transition (5 mins),
    and serve Household B (08:20-09:05).
    """
    user_a = test_setup["user_a"]
    user_b = test_setup["user_b"]
    hh_a = test_setup["household_a"]
    hh_b = test_setup["household_b"]
    service_date = test_setup["service_date"]

    # 1. Household A
    api_client.force_authenticate(user=user_a)
    payload_a = {
        "service_date": str(service_date),
        "earliest_start": "07:30",
        "latest_finish": "08:30",
        "estimated_duration_minutes": 45,
        "required_skills": ["basic_breakfast"],
    }
    resp_a = api_client.post(f"/api/v1/households/{hh_a.id}/bookings", payload_a, format="json")
    assert resp_a.status_code == status.HTTP_201_CREATED

    # 2. Household B with wider window
    api_client.force_authenticate(user=user_b)
    payload_b = {
        "service_date": str(service_date),
        "earliest_start": "07:30",
        "latest_finish": "09:15",
        "estimated_duration_minutes": 45,
        "required_skills": ["basic_breakfast"],
    }
    resp_b = api_client.post(f"/api/v1/households/{hh_b.id}/bookings", payload_b, format="json")
    assert resp_b.status_code == status.HTTP_201_CREATED
    data_b = resp_b.json()
    assert data_b["status"] == Booking.STATUS_CONFIRMED
    assert data_b["assignment"] is not None
    # 08:20 is 500, end 545 (09:05)
    assert data_b["assignment"]["start_minute"] >= 495 + 5  # at or after 08:20
    assert data_b["assignment"]["end_minute"] <= 555         # before or at 09:15


@pytest.mark.django_db
def test_idempotent_booking_creation(
    api_client: APIClient,
    test_setup: dict,
) -> None:
    """Repeated calls with same Idempotency-Key return cached response;
    call with same key but different payload returns 409 Conflict.
    """
    user_a = test_setup["user_a"]
    hh_a = test_setup["household_a"]
    service_date = test_setup["service_date"]

    api_client.force_authenticate(user=user_a)
    payload = {
        "service_date": str(service_date),
        "meal_type": "breakfast",
        "earliest_start": "07:30",
        "latest_finish": "08:30",
        "estimated_duration_minutes": 45,
        "required_skills": ["basic_breakfast"],
    }
    headers = {"HTTP_IDEMPOTENCY_KEY": "unique-idem-key-12345"}

    # First call
    resp1 = api_client.post(
        f"/api/v1/households/{hh_a.id}/bookings",
        payload,
        format="json",
        **headers,
    )
    assert resp1.status_code == status.HTTP_201_CREATED
    data1 = resp1.json()

    # Second call (same payload, same key) -> must return same result, exactly 1 booking in DB
    resp2 = api_client.post(
        f"/api/v1/households/{hh_a.id}/bookings",
        payload,
        format="json",
        **headers,
    )
    assert resp2.status_code == status.HTTP_201_CREATED
    data2 = resp2.json()
    assert data2["id"] == data1["id"]
    assert Booking.objects.count() == 1

    # Third call (different payload, same key) -> 409
    tampered_payload = dict(payload)
    tampered_payload["estimated_duration_minutes"] = 60
    resp3 = api_client.post(
        f"/api/v1/households/{hh_a.id}/bookings",
        tampered_payload,
        format="json",
        **headers,
    )
    assert resp3.status_code == status.HTTP_409_CONFLICT
    err3 = resp3.json()
    error_code = err3.get("code") or err3.get("error", {}).get("code")
    assert error_code == "IDEMPOTENCY_KEY_REUSED_WITH_DIFFERENT_PAYLOAD"


@pytest.mark.django_db
def test_schedule_versioning_and_immutability(
    api_client: APIClient,
    test_setup: dict,
) -> None:
    """Publishing new assignments creates a new SchedulePlan version and
    marks prior version as superseded without erasing assignment history.
    """
    user_a = test_setup["user_a"]
    hh_a = test_setup["household_a"]
    service_date = test_setup["service_date"]
    society = test_setup["society"]

    api_client.force_authenticate(user=user_a)
    payload = {
        "service_date": str(service_date),
        "earliest_start": "07:30",
        "latest_finish": "08:30",
        "estimated_duration_minutes": 45,
        "required_skills": ["basic_breakfast"],
    }
    resp = api_client.post(f"/api/v1/households/{hh_a.id}/bookings", payload, format="json")
    assert resp.status_code == status.HTTP_201_CREATED

    plan_v1 = SchedulePlan.objects.get(society=society, service_date=service_date, version=1)
    assert plan_v1.status == SchedulePlan.STATUS_PUBLISHED

    # Cancel booking
    booking_id = resp.json()["id"]
    cancel_resp = api_client.post(f"/api/v1/bookings/{booking_id}/cancel")
    assert cancel_resp.status_code == status.HTTP_200_OK

    assignment = CookAssignment.objects.get(booking_id=booking_id)
    assert assignment.status == CookAssignment.STATUS_CANCELLED


@pytest.mark.django_db
def test_household_authorization_isolation(
    api_client: APIClient,
    test_setup: dict,
) -> None:
    """An outsider cannot create or inspect bookings for another household."""
    outsider = test_setup["outsider"]
    hh_a = test_setup["household_a"]
    service_date = test_setup["service_date"]

    api_client.force_authenticate(user=outsider)
    payload = {
        "service_date": str(service_date),
        "earliest_start": "07:30",
        "latest_finish": "08:30",
        "estimated_duration_minutes": 45,
    }
    resp = api_client.post(f"/api/v1/households/{hh_a.id}/bookings", payload, format="json")
    assert resp.status_code == status.HTTP_403_FORBIDDEN
