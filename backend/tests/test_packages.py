"""Tests for Phase 9: Package Management, Subscription Entitlements, and Optimizer Integration."""

from __future__ import annotations

import datetime

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.bookings.models import (
    Booking,
    HouseholdPackageSubscription,
    PackageBookingLink,
    PackagePlan,
)
from apps.bookings.services.package_service import PackageService
from apps.communities.models import Building, Society
from apps.cooks.models import CookAvailability, CookProfile, Skill
from apps.households.models import Household, HouseholdMember
from apps.identity.models import Role, User, UserRole


@pytest.fixture
def package_setup() -> dict:
    """Fixture establishing society, household, verified cook, and package plans."""
    soc = Society.objects.create(name="Greenwood Society", address="Sector 5, HSR Layout, Bengaluru")
    bld = Building.objects.create(society=soc, name="Tower 1")
    hh = Household.objects.create(society=soc, building=bld, apartment_label="201")

    # Resident
    resident = User.objects.create_user(email="resident.pkg@example.com", password="Pass123!Safe")
    role_res, _ = Role.objects.get_or_create(code=Role.HOUSEHOLD_MEMBER)
    UserRole.objects.create(user=resident, role=role_res)
    HouseholdMember.objects.create(household=hh, user=resident, role=HouseholdMember.ROLE_PRIMARY)

    # Admin
    admin = User.objects.create_superuser(email="admin.pkg@example.com", password="AdminPass123!")

    # Cook with daily availability 07:00 to 11:00 (420..660)
    cook_user = User.objects.create_user(email="cook.pkg@example.com", password="Pass123!Safe")
    role_cook, _ = Role.objects.get_or_create(code=Role.COOK)
    UserRole.objects.create(user=cook_user, role=role_cook)
    cook = CookProfile.objects.create(
        user=cook_user,
        verification_status=CookProfile.VERIFICATION_VERIFIED,
        active_status=True,
    )
    cook.societies.add(soc)
    breakfast_skill, _ = Skill.objects.get_or_create(code="basic_breakfast", defaults={"name": "Basic Breakfast"})

    # Set cook working windows for every day (0..6)
    for day in range(7):
        CookAvailability.objects.create(
            cook=cook,
            weekday=day,
            start_minute=420,
            end_minute=660,
        )

    # Weekly Package Plan: 5 visits over 7 days
    weekly_plan = PackagePlan.objects.create(
        society=soc,
        name="Weekly Breakfast Standard",
        code="PKG_WEEKLY_BK_5D",
        plan_type=PackagePlan.PLAN_WEEKLY,
        visit_frequency_per_week=5,
        total_visits=5,
        validity_days=7,
        price_minor_units=95000,
        meal_type=Booking.MEAL_BREAKFAST,
        default_duration_minutes=45,
        max_pause_days=7,
        is_active=True,
    )

    # Monthly Package Plan: 20 visits over 30 days
    monthly_plan = PackagePlan.objects.create(
        society=soc,
        name="Monthly Breakfast Premium",
        code="PKG_MONTHLY_BK_20D",
        plan_type=PackagePlan.PLAN_MONTHLY,
        visit_frequency_per_week=5,
        total_visits=20,
        validity_days=30,
        price_minor_units=350000,
        meal_type=Booking.MEAL_BREAKFAST,
        default_duration_minutes=45,
        max_pause_days=14,
        is_active=True,
    )

    return {
        "society": soc,
        "household": hh,
        "resident": resident,
        "admin": admin,
        "cook": cook,
        "weekly_plan": weekly_plan,
        "monthly_plan": monthly_plan,
    }


@pytest.mark.django_db
def test_package_subscription_generates_optimizer_confirmed_bookings(package_setup: dict) -> None:
    """Subscribing to a weekly package generates 5 visits and commits assignments via CP-SAT."""
    hh = package_setup["household"]
    resident = package_setup["resident"]
    plan = package_setup["weekly_plan"]

    # Start next Monday: 2027-02-15 is Monday
    start_date = datetime.date(2027, 2, 15)

    sub, bookings = PackageService.subscribe_household(
        household=hh,
        package_plan=plan,
        start_date=start_date,
        preferred_weekdays=[0, 1, 2, 3, 4],  # Mon-Fri
        preferred_start_minute=450,  # 07:30
        preferred_end_minute=540,  # 09:00
        actor=resident,
    )

    assert sub.status == HouseholdPackageSubscription.STATUS_ACTIVE
    assert sub.total_entitled_visits == 5
    assert sub.used_visits == 0
    assert sub.remaining_visits == 5
    assert len(bookings) == 5

    # Verify all bookings have dates within the 7-day validity window
    for b in bookings:
        assert start_date <= b.service_date <= sub.end_date
        assert b.meal_type == Booking.MEAL_BREAKFAST
        assert b.duration_minutes == 45
        # With cook available, each booking is confirmed by CP-SAT solver
        assert b.status == Booking.STATUS_CONFIRMED
        assert b.assignments.filter(status="CONFIRMED").exists()
        assert PackageBookingLink.objects.filter(subscription=sub, booking=b).exists()


@pytest.mark.django_db
def test_package_purchased_never_bypasses_optimizer_when_cook_unavailable(package_setup: dict) -> None:
    """A purchased package must NEVER bypass the scheduling engine or force an invalid assignment."""
    hh = package_setup["household"]
    resident = package_setup["resident"]
    plan = package_setup["weekly_plan"]
    cook = package_setup["cook"]

    # Deactivate the cook so no cooks are available
    cook.active_status = False
    cook.save()

    start_date = datetime.date(2027, 2, 15)

    sub, bookings = PackageService.subscribe_household(
        household=hh,
        package_plan=plan,
        start_date=start_date,
        preferred_weekdays=[0, 1, 2, 3, 4],
        actor=resident,
    )

    assert sub.status == HouseholdPackageSubscription.STATUS_ACTIVE
    assert len(bookings) == 5

    # Since cook is unavailable, bookings MUST NOT be confirmed (they remain UNFULFILLED or PENDING)
    for b in bookings:
        assert b.status != Booking.STATUS_CONFIRMED
        assert not b.assignments.filter(status="CONFIRMED").exists()


@pytest.mark.django_db
def test_package_subscription_pause_and_resume(package_setup: dict) -> None:
    """Pausing an active package extends end date and cancels pending visits during pause window."""
    hh = package_setup["household"]
    resident = package_setup["resident"]
    plan = package_setup["weekly_plan"]

    start_date = datetime.date(2027, 2, 15)
    sub, bookings = PackageService.subscribe_household(
        household=hh,
        package_plan=plan,
        start_date=start_date,
        preferred_weekdays=[0, 1, 2, 3, 4],
        actor=resident,
    )
    orig_end_date = sub.end_date

    # Pause subscription for 5 days
    paused_sub = PackageService.pause_subscription(
        subscription=sub,
        pause_days=5,
        actor=resident,
    )
    assert paused_sub.status == HouseholdPackageSubscription.STATUS_PAUSED
    assert paused_sub.paused_at is not None
    assert paused_sub.pause_resumes_at is not None
    assert paused_sub.end_date == orig_end_date + datetime.timedelta(days=5)

    # Resume subscription
    resumed_sub = PackageService.resume_subscription(subscription=paused_sub, actor=resident)
    assert resumed_sub.status == HouseholdPackageSubscription.STATUS_ACTIVE
    assert resumed_sub.paused_at is None
    assert resumed_sub.pause_resumes_at is None


@pytest.mark.django_db
def test_package_subscription_cancel_terminates_future_visits(package_setup: dict) -> None:
    """Cancelling a package cancels remaining future visits and records cancellation reason."""
    hh = package_setup["household"]
    resident = package_setup["resident"]
    plan = package_setup["weekly_plan"]

    start_date = datetime.date(2027, 2, 15)
    sub, bookings = PackageService.subscribe_household(
        household=hh,
        package_plan=plan,
        start_date=start_date,
        preferred_weekdays=[0, 1, 2, 3, 4],
        actor=resident,
    )

    cancelled_sub = PackageService.cancel_subscription(
        subscription=sub,
        reason="Family moving out of city",
        actor=resident,
    )
    assert cancelled_sub.status == HouseholdPackageSubscription.STATUS_CANCELLED
    assert cancelled_sub.cancelled_visits > 0

    for b in bookings:
        b.refresh_from_db()
        assert b.status == Booking.STATUS_CANCELLED


@pytest.mark.django_db
def test_package_api_subscribe_and_detail(package_setup: dict) -> None:
    """Test full REST API workflow: listing plans, subscribing, and querying entitlement."""
    hh = package_setup["household"]
    resident = package_setup["resident"]
    plan = package_setup["weekly_plan"]

    client = APIClient()
    client.force_authenticate(user=resident)

    # 1. Query package plans
    plans_resp = client.get("/api/v1/packages/plans")
    assert plans_resp.status_code == status.HTTP_200_OK
    assert len(plans_resp.json()) >= 2

    # 2. Subscribe household to weekly plan
    sub_payload = {
        "package_plan_id": str(plan.id),
        "start_date": "2027-02-15",
        "preferred_weekdays": [0, 1, 2, 3, 4],
        "preferred_start": "07:30",
        "preferred_end": "09:00",
    }
    sub_resp = client.post(f"/api/v1/households/{hh.id}/packages/subscribe", sub_payload, format="json")
    assert sub_resp.status_code == status.HTTP_201_CREATED
    sub_id = sub_resp.json()["id"]
    assert sub_resp.json()["total_entitled_visits"] == 5
    assert len(sub_resp.json()["generated_bookings"]) == 5

    # 3. Retrieve subscription details with visit checklist
    detail_resp = client.get(f"/api/v1/packages/subscriptions/{sub_id}")
    assert detail_resp.status_code == status.HTTP_200_OK
    assert detail_resp.json()["remaining_visits"] == 5
    assert len(detail_resp.json()["visits"]) == 5

