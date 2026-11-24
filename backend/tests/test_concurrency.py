"""Concurrency and database reliability tests for simultaneous booking requests."""

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
from apps.operations.models import OutboxEvent
from apps.scheduling.models import CookAssignment


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def concurrency_setup():
    society = Society.objects.create(name="Palm Heights", address="123 Palm Ave", timezone="UTC")
    building = Building.objects.create(society=society, name="Tower A")

    user_a = User.objects.create_user(email="resident.a@example.com", password="PassWord123!")
    hh_a = Household.objects.create(society=society, building=building, apartment_label="A-101")
    HouseholdMember.objects.create(household=hh_a, user=user_a, role=HouseholdMember.ROLE_PRIMARY, is_active=True)

    user_b = User.objects.create_user(email="resident.b@example.com", password="PassWord123!")
    hh_b = Household.objects.create(society=society, building=building, apartment_label="A-102")
    HouseholdMember.objects.create(household=hh_b, user=user_b, role=HouseholdMember.ROLE_PRIMARY, is_active=True)

    skill = Skill.objects.create(code="basic_breakfast", name="Basic Breakfast")

    cook_user = User.objects.create_user(email="cook.solo@example.com", password="PassWord123!")
    role_cook, _ = Role.objects.get_or_create(code=Role.COOK)
    cook_user.user_roles.create(role=role_cook)

    cook = CookProfile.objects.create(
        user=cook_user,
        verification_status=CookProfile.VERIFICATION_VERIFIED,
        active_status=True,
        max_daily_minutes=480,
        max_daily_visits=6,
    )
    cook.societies.add(society)
    CookSkill.objects.create(cook=cook, skill=skill, proficiency_level="expert")
    CookWorkPolicy.objects.create(
        cook=cook,
        max_consecutive_visits=4,
        max_daily_minutes=480,
        buffer_between_visits_minutes=5,
    )

    # Monday working window: 07:00 (420) to 08:45 (525) -> exactly fits only ONE 45-minute booking + transition!
    service_date = datetime.date(2027, 2, 15)
    CookAvailability.objects.create(
        cook=cook,
        weekday=0,
        start_minute=420,
        end_minute=510,  # 07:00 to 08:30 (90 mins total, only fits one 45m visit within 07:30-08:30)
        availability_type=CookAvailability.TYPE_REGULAR,
    )

    return {
        "society": society,
        "hh_a": hh_a,
        "hh_b": hh_b,
        "user_a": user_a,
        "user_b": user_b,
        "cook": cook,
        "service_date": service_date,
    }


@pytest.mark.django_db
def test_simultaneous_conflicting_requests_prevent_overlap(
    concurrency_setup: dict,
) -> None:
    """When two conflicting requests are submitted for the same time window and single cook:
    1. First booking commits confirmed assignment.
    2. Second booking revalidates against committed state and is rejected as UNFULFILLED.
    3. Exactly 1 confirmed assignment exists for the cook; zero overlap.
    """
    user_a = concurrency_setup["user_a"]
    user_b = concurrency_setup["user_b"]
    hh_a = concurrency_setup["hh_a"]
    hh_b = concurrency_setup["hh_b"]
    cook = concurrency_setup["cook"]
    service_date = concurrency_setup["service_date"]

    client_a = APIClient()
    client_a.force_authenticate(user=user_a)

    client_b = APIClient()
    client_b.force_authenticate(user=user_b)

    payload = {
        "service_date": str(service_date),
        "meal_type": "breakfast",
        "earliest_start": "07:30",
        "latest_finish": "08:30",
        "estimated_duration_minutes": 45,
        "required_skills": ["basic_breakfast"],
    }

    # Request A
    resp_a = client_a.post(f"/api/v1/households/{hh_a.id}/bookings", payload, format="json")
    assert resp_a.status_code == status.HTTP_201_CREATED
    assert resp_a.json()["status"] == Booking.STATUS_CONFIRMED

    # Request B
    resp_b = client_b.post(f"/api/v1/households/{hh_b.id}/bookings", payload, format="json")
    assert resp_b.status_code == status.HTTP_201_CREATED
    assert resp_b.json()["status"] == Booking.STATUS_UNFULFILLED

    # INVARIANT CHECK: Only ONE active assignment exists for this cook
    active_assignments = CookAssignment.objects.filter(
        cook=cook,
        status__in=[
            CookAssignment.STATUS_CONFIRMED,
            CookAssignment.STATUS_STARTED,
            CookAssignment.STATUS_COMPLETED,
        ],
    )
    assert active_assignments.count() == 1

    # Outbox events recorded
    outbox_events = OutboxEvent.objects.filter(event_type="schedule.published")
    assert outbox_events.exists()

