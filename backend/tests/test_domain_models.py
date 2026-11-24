"""Tests for Phase 2 domain models, constraints, and validation invariants."""

from __future__ import annotations

import datetime
import uuid

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.communities.models import Apartment, Building, Society
from apps.cooks.models import (
    CookAvailability,
    CookBreak,
    CookLeave,
    CookProfile,
    CookSkill,
    CookWorkPolicy,
    Skill,
)
from apps.households.models import Household, HouseholdMember
from apps.identity.models import Role, User, UserRole


@pytest.mark.django_db
def test_user_and_role_creation() -> None:
    user = User.objects.create_user(email="alice@example.com", password="SecretPassword123!")
    assert isinstance(user.id, uuid.UUID)
    assert user.email == "alice@example.com"
    assert user.is_active is True
    assert user.check_password("SecretPassword123!")

    role = Role.objects.create(code=Role.COOK, name="Cook")
    UserRole.objects.create(user=user, role=role)

    assert user.has_role(Role.COOK) is True
    assert user.has_role(Role.PLATFORM_ADMIN) is False

    # Unique constraint on (user, role)
    with transaction.atomic(), pytest.raises(IntegrityError):
        UserRole.objects.create(user=user, role=role)


@pytest.mark.django_db
def test_community_hierarchy_and_uniqueness() -> None:
    society = Society.objects.create(name="Palm Grove", address="123 Main St", timezone="Asia/Kolkata")
    assert isinstance(society.id, uuid.UUID)

    building_a = Building.objects.create(society=society, name="Tower A", code="TWR-A")
    apartment_101 = Apartment.objects.create(building=building_a, number="101", floor=1)

    assert apartment_101.building == building_a
    assert building_a.society == society

    # Duplicate building name in same society must fail
    with transaction.atomic(), pytest.raises(IntegrityError):
        Building.objects.create(society=society, name="Tower A")

    # Duplicate apartment in same building must fail
    with transaction.atomic(), pytest.raises(IntegrityError):
        Apartment.objects.create(building=building_a, number="101")


@pytest.mark.django_db
def test_household_and_membership_invariants() -> None:
    society1 = Society.objects.create(name="Palm Grove 1", address="123 Palm Ave")
    society2 = Society.objects.create(name="Palm Grove 2", address="456 Palm Ave")

    building_soc1 = Building.objects.create(society=society1, name="Tower A")
    building_soc2 = Building.objects.create(society=society2, name="Tower B")

    # Valid household
    household = Household.objects.create(
        society=society1,
        building=building_soc1,
        apartment_label="404",
    )
    assert household.status == Household.STATUS_ACTIVE

    # Cross-society building validation must fail
    with pytest.raises(ValidationError):
        Household.objects.create(
            society=society1,
            building=building_soc2,
            apartment_label="405",
        )

    # Membership creation
    user = User.objects.create_user(email="resident@example.com", password="PassWord123!")
    membership = HouseholdMember.objects.create(
        household=household,
        user=user,
        role=HouseholdMember.ROLE_PRIMARY,
    )
    assert membership.role == "primary"

    # Duplicate membership for same (household, user) must violate unique constraint
    with transaction.atomic(), pytest.raises(IntegrityError):
        HouseholdMember.objects.create(
            household=household,
            user=user,
            role=HouseholdMember.ROLE_MEMBER,
        )


@pytest.mark.django_db
def test_cook_profile_skills_and_work_policy() -> None:
    user = User.objects.create_user(email="chef@example.com", password="ChefPassword123!")
    society = Society.objects.create(name="Green Heights", address="789 Green Rd")

    cook = CookProfile.objects.create(
        user=user,
        verification_status=CookProfile.VERIFICATION_VERIFIED,
        max_daily_minutes=480,
        max_daily_visits=5,
    )
    cook.societies.add(society)
    assert cook.is_eligible_to_work is True

    skill = Skill.objects.create(code="basic_breakfast", name="Basic Breakfast")
    cook_skill = CookSkill.objects.create(
        cook=cook,
        skill=skill,
        proficiency_level=CookSkill.LEVEL_EXPERT,
    )
    assert cook_skill.proficiency_level == "expert"

    # Duplicate skill assignment for same cook
    with transaction.atomic(), pytest.raises(IntegrityError):
        CookSkill.objects.create(cook=cook, skill=skill)

    # Work policy
    policy = CookWorkPolicy.objects.create(
        cook=cook,
        max_consecutive_visits=3,
        max_daily_minutes=420,
        buffer_between_visits_minutes=5,
    )
    assert policy.buffer_between_visits_minutes == 5


@pytest.mark.django_db
def test_cook_availability_break_and_leave_constraints() -> None:
    user = User.objects.create_user(email="cook_alexa@example.com", password="AlexaPassword123!")
    cook = CookProfile.objects.create(
        user=user,
        verification_status=CookProfile.VERIFICATION_VERIFIED,
    )

    # Valid regular weekday availability (07:00 to 11:00 -> 420 to 660)
    avail = CookAvailability.objects.create(
        cook=cook,
        weekday=0,
        start_minute=420,
        end_minute=660,
    )
    assert avail.start_minute == 420

    # Inverted time window must be rejected
    with transaction.atomic(), pytest.raises((ValidationError, IntegrityError)):
        CookAvailability.objects.create(
            cook=cook,
            weekday=1,
            start_minute=700,
            end_minute=600,
        )

    # Valid break
    cook_break = CookBreak.objects.create(
        cook=cook,
        recurring_weekday=0,
        start_minute=540,
        end_minute=570,
        reason="Tea Break",
    )
    assert cook_break.end_minute == 570

    # Inverted break must be rejected
    with transaction.atomic(), pytest.raises((ValidationError, IntegrityError)):
        CookBreak.objects.create(
            cook=cook,
            recurring_weekday=0,
            start_minute=600,
            end_minute=550,
        )

    # Valid leave
    leave = CookLeave.objects.create(
        cook=cook,
        start_date=datetime.date(2027, 2, 10),
        end_date=datetime.date(2027, 2, 15),
        reason="Annual vacation",
    )
    assert leave.status == "approved"

    # Inverted leave dates must be rejected
    with transaction.atomic(), pytest.raises((ValidationError, IntegrityError)):
        CookLeave.objects.create(
            cook=cook,
            start_date=datetime.date(2027, 2, 20),
            end_date=datetime.date(2027, 2, 15),
        )
