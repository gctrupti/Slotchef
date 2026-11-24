"""Tests for Phase 8: Payment Foundation, Pricing Rules, and Price Breakdown Snapshots."""

from __future__ import annotations

import datetime
import decimal

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.bookings.models import Booking
from apps.communities.models import Building, Society
from apps.finance.models import (
    PlatformCommissionConfig,
    ServicePricingRule,
)
from apps.finance.services.pricing_calculator import PricingCalculatorService
from apps.households.models import Household, HouseholdMember
from apps.identity.models import Role, User, UserRole


@pytest.fixture
def pricing_setup() -> dict:
    """Fixture establishing society, users, pricing rule, and commission policy."""
    # Society & Building
    soc = Society.objects.create(name="Prestige Heights", address="123 Ring Road, Bengaluru")
    bld = Building.objects.create(society=soc, name="Block A")
    hh = Household.objects.create(society=soc, building=bld, apartment_label="101")

    # Users
    resident = User.objects.create_user(email="resident.pricing@example.com", password="Pass123!Safe")
    admin = User.objects.create_superuser(email="admin.pricing@example.com", password="AdminPass123!")
    unauthorized = User.objects.create_user(email="stranger.pricing@example.com", password="Pass123!Safe")

    role_res, _ = Role.objects.get_or_create(code=Role.HOUSEHOLD_MEMBER)
    UserRole.objects.create(user=resident, role=role_res)
    HouseholdMember.objects.create(household=hh, user=resident, role=HouseholdMember.ROLE_PRIMARY)

    # Active pricing rule for Prestige Heights
    rule = ServicePricingRule.objects.create(
        society=soc,
        name="Prestige Standard Per-Visit",
        code="PRESTIGE_STD_V1",
        pricing_type=ServicePricingRule.TYPE_PER_VISIT,
        base_fee_minor_units=25000,  # 250 INR base
        per_minute_rate_minor_units=300,  # 3.00 INR / min
        breakfast_multiplier=decimal.Decimal("1.00"),
        lunch_multiplier=decimal.Decimal("1.25"),
        dinner_multiplier=decimal.Decimal("1.30"),
        currency="INR",
        is_active=True,
    )

    # Commission policy: 20%
    commission = PlatformCommissionConfig.objects.create(
        society=soc,
        commission_type=PlatformCommissionConfig.TYPE_PERCENTAGE,
        percentage_rate=decimal.Decimal("20.00"),
        is_active=True,
    )

    return {
        "society": soc,
        "household": hh,
        "resident": resident,
        "admin": admin,
        "unauthorized": unauthorized,
        "rule": rule,
        "commission": commission,
    }


@pytest.mark.django_db
def test_pricing_calculator_math_and_snapshot(pricing_setup: dict) -> None:
    """Validate mathematical exactness of pricing engine and snapshot persistence."""
    hh = pricing_setup["household"]
    resident = pricing_setup["resident"]
    rule = pricing_setup["rule"]
    comm = pricing_setup["commission"]

    booking = Booking.objects.create(
        household=hh,
        requested_by=resident,
        service_date=datetime.date(2027, 3, 10),
        earliest_start_minute=480,  # 08:00
        latest_finish_minute=540,  # 09:00
        duration_minutes=40,  # 40 mins
        meal_type=Booking.MEAL_LUNCH,
        status=Booking.STATUS_PENDING,
    )

    breakdown = PricingCalculatorService.calculate_price_breakdown(booking=booking, persist=True)

    # Expected calculations:
    # Base fee: 25000 paise
    # Duration fee: 40 mins * 300 paise = 12000 paise
    # Raw sum: 25000 + 12000 = 37000 paise
    # Lunch multiplier: 1.25 -> 37000 * 1.25 = 46250 paise
    # Platform commission (20%): 46250 * 0.20 = 9250 paise
    # Cook earnings: 46250 - 9250 = 37000 paise
    # Total customer amount: 46250 paise
    assert breakdown.base_fee_minor_units == 25000
    assert breakdown.duration_fee_minor_units == 12000
    assert float(breakdown.meal_multiplier) == 1.25
    assert breakdown.subtotal_minor_units == 46250
    assert breakdown.platform_commission_minor_units == 9250
    assert breakdown.cook_earnings_minor_units == 37000
    assert breakdown.total_amount_minor_units == 46250
    assert breakdown.currency == "INR"
    assert breakdown.pricing_rule == rule
    assert breakdown.commission_config == comm

    # Metadata audit trail is complete
    meta = breakdown.snapshot_metadata
    assert meta["duration_minutes"] == 40
    assert meta["meal_type"] == "lunch"
    assert meta["rule_code"] == "PRESTIGE_STD_V1"
    assert meta["commission_rate"] == 20.0


@pytest.mark.django_db
def test_price_estimate_api_public(pricing_setup: dict) -> None:
    """Public / unauthenticated price estimation endpoint provides upfront pricing breakdown."""
    soc = pricing_setup["society"]
    client = APIClient()

    payload = {
        "society_id": str(soc.id),
        "duration_minutes": 60,
        "meal_type": "dinner",
        "pricing_type": "per_visit",
    }
    resp = client.post("/api/v1/pricing/estimate", payload, format="json")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()

    # Base: 25000, Duration: 60 * 300 = 18000. Raw = 43000
    # Dinner multiplier: 1.30 -> 43000 * 1.30 = 55900
    # Commission 20% -> 11180, Cook -> 44720
    assert data["duration_minutes"] == 60
    assert data["meal_type"] == "dinner"
    assert data["subtotal_minor_units"] == 55900
    assert data["platform_commission_minor_units"] == 11180
    assert data["cook_earnings_minor_units"] == 44720
    assert data["total_amount_minor_units"] == 55900


@pytest.mark.django_db
def test_pricing_rules_rbac_and_crud(pricing_setup: dict) -> None:
    """Only admins can create or mutate pricing rules; residents can read active rules."""
    soc = pricing_setup["society"]
    admin = pricing_setup["admin"]
    resident = pricing_setup["resident"]

    # 1. Resident can view active rules
    client_res = APIClient()
    client_res.force_authenticate(user=resident)
    get_resp = client_res.get(f"/api/v1/pricing/rules?society_id={soc.id}")
    assert get_resp.status_code == status.HTTP_200_OK
    assert len(get_resp.json()) >= 1

    # 2. Resident cannot create pricing rules (403 Forbidden)
    post_payload = {
        "society": str(soc.id),
        "name": "Unauthorized Rule",
        "code": "HACK_RULE",
        "pricing_type": "per_visit",
        "base_fee_minor_units": 1000,
        "per_minute_rate_minor_units": 10,
    }
    deny_resp = client_res.post("/api/v1/pricing/rules", post_payload, format="json")
    assert deny_resp.status_code == status.HTTP_403_FORBIDDEN

    # 3. Admin can create new pricing rule
    client_admin = APIClient()
    client_admin.force_authenticate(user=admin)
    create_resp = client_admin.post("/api/v1/pricing/rules", post_payload, format="json")
    assert create_resp.status_code == status.HTTP_201_CREATED
    assert create_resp.json()["code"] == "HACK_RULE"


@pytest.mark.django_db
def test_booking_creation_automatically_snapshots_pricing(pricing_setup: dict) -> None:
    """End-to-end booking creation generates and attaches price breakdown to response."""
    hh = pricing_setup["household"]
    resident = pricing_setup["resident"]
    unauth = pricing_setup["unauthorized"]

    client = APIClient()
    client.force_authenticate(user=resident)

    payload = {
        "service_date": "2027-03-15",
        "earliest_start": "07:30",
        "latest_finish": "08:30",
        "estimated_duration_minutes": 45,
        "meal_type": "breakfast",
        "required_skills": [],
    }
    resp = client.post(f"/api/v1/households/{hh.id}/bookings", payload, format="json")
    assert resp.status_code == status.HTTP_201_CREATED
    booking_id = resp.json()["id"]

    # Verify price breakdown is included in booking detail response
    assert "price_breakdown" in resp.json()
    bd = resp.json()["price_breakdown"]
    assert bd is not None
    assert bd["currency"] == "INR"
    assert bd["total_amount_minor_units"] > 0
    assert bd["cook_earnings_minor_units"] > 0
    assert bd["platform_commission_minor_units"] > 0

    # Dedicated breakdown endpoint permits authorized resident
    bd_resp = client.get(f"/api/v1/bookings/{booking_id}/price-breakdown")
    assert bd_resp.status_code == status.HTTP_200_OK
    assert bd_resp.json()["subtotal_minor_units"] == bd["subtotal_minor_units"]

    # Unauthorized stranger cannot access booking breakdown
    client_stranger = APIClient()
    client_stranger.force_authenticate(user=unauth)
    stranger_resp = client_stranger.get(f"/api/v1/bookings/{booking_id}/price-breakdown")
    assert stranger_resp.status_code == status.HTTP_403_FORBIDDEN
