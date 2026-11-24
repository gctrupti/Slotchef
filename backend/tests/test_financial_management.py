"""Tests for Phase 10: Payment and Financial Management (Online, COD, Commission Ledger, Payouts)."""

from __future__ import annotations

import datetime
import decimal
import hashlib
import hmac

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.bookings.models import Booking
from apps.communities.models import Building, Society
from apps.cooks.models import CookProfile
from apps.finance.models import (
    CashCollectionRecord,
    CommissionLedger,
    PaymentOrder,
    PaymentTransaction,
    PlatformCommissionConfig,
    ServicePricingRule,
)
from apps.finance.providers.payment_provider import MockPaymentProvider
from apps.finance.services.pricing_calculator import PricingCalculatorService
from apps.households.models import Household, HouseholdMember
from apps.identity.models import Role, User, UserRole
from apps.scheduling.models import CookAssignment


@pytest.fixture
def finance_setup() -> dict:
    """Fixture establishing society, household, cook, confirmed booking, and pricing tier."""
    soc = Society.objects.create(name="Palm Grove Society", address="Sarjapur Road, Bengaluru")
    bld = Building.objects.create(society=soc, name="Block B")
    hh = Household.objects.create(society=soc, building=bld, apartment_label="302")

    # Resident
    resident = User.objects.create_user(email="resident.fin@example.com", password="Pass123!Safe")
    role_res, _ = Role.objects.get_or_create(code=Role.HOUSEHOLD_MEMBER)
    UserRole.objects.create(user=resident, role=role_res)
    HouseholdMember.objects.create(household=hh, user=resident, role=HouseholdMember.ROLE_PRIMARY)

    # Cook
    cook_user = User.objects.create_user(email="cook.fin@example.com", password="Pass123!Safe")
    role_cook, _ = Role.objects.get_or_create(code=Role.COOK)
    UserRole.objects.create(user=cook_user, role=role_cook)
    cook = CookProfile.objects.create(
        user=cook_user,
        verification_status=CookProfile.VERIFICATION_VERIFIED,
        active_status=True,
    )
    cook.societies.add(soc)

    # Admin
    admin = User.objects.create_superuser(email="admin.fin@example.com", password="AdminPass123!")

    # Active Pricing Rule & 15% Platform Commission
    ServicePricingRule.objects.create(
        society=soc,
        name="Palm Grove Standard",
        code="PG_STD_V1",
        base_fee_minor_units=20000,  # 200 INR
        per_minute_rate_minor_units=200,  # 2 INR / min
        breakfast_multiplier=decimal.Decimal("1.00"),
        currency="INR",
        is_active=True,
    )
    PlatformCommissionConfig.objects.create(
        society=soc,
        commission_type=PlatformCommissionConfig.TYPE_PERCENTAGE,
        percentage_rate=decimal.Decimal("15.00"),
        is_active=True,
    )

    # Create Booking
    booking = Booking.objects.create(
        household=hh,
        requested_by=resident,
        service_date=datetime.date(2027, 2, 20),
        earliest_start_minute=480,
        latest_finish_minute=540,
        duration_minutes=45,
        meal_type=Booking.MEAL_BREAKFAST,
        status=Booking.STATUS_CONFIRMED,
    )
    PricingCalculatorService.calculate_price_breakdown(booking, persist=True)

    # Assign Cook
    from apps.scheduling.models import SchedulePlan
    plan = SchedulePlan.objects.create(society=soc, service_date=booking.service_date, version=1)
    start_dt = timezone_aware_datetime(booking.service_date, 480)
    end_dt = timezone_aware_datetime(booking.service_date, 525)
    assignment = CookAssignment.objects.create(
        schedule_plan=plan,
        booking=booking,
        cook=cook,
        start_at=start_dt,
        end_at=end_dt,
        start_minute=480,
        end_minute=525,
        status=CookAssignment.STATUS_CONFIRMED,
    )

    return {
        "society": soc,
        "household": hh,
        "resident": resident,
        "cook": cook,
        "admin": admin,
        "booking": booking,
        "assignment": assignment,
    }


def timezone_aware_datetime(d: datetime.date, minute: int) -> datetime.datetime:
    hour = minute // 60
    mn = minute % 60
    return datetime.datetime(d.year, d.month, d.day, hour, mn, tzinfo=datetime.UTC)


@pytest.mark.django_db
def test_online_payment_order_create_and_signature_verification(finance_setup: dict) -> None:
    """Create online payment order and verify gateway signature successfully."""
    resident = finance_setup["resident"]
    booking = finance_setup["booking"]

    client = APIClient()
    client.force_authenticate(user=resident)

    # 1. Create payment order
    order_payload = {"booking_id": str(booking.id)}
    order_resp = client.post("/api/v1/payments/orders", order_payload, format="json")
    assert order_resp.status_code == status.HTTP_201_CREATED
    order_data = order_resp.json()
    provider_order_id = order_data["provider_order_id"]
    assert order_data["status"] == "created"
    assert order_data["amount_minor_units"] == booking.price_breakdown.total_amount_minor_units

    # 2. Reject verification with forged/invalid signature
    bad_verify_payload = {
        "provider_order_id": provider_order_id,
        "provider_payment_id": "pay_mock_12345",
        "signature": "forged_signature_invalid",
    }
    bad_resp = client.post("/api/v1/payments/verify", bad_verify_payload, format="json")
    assert bad_resp.status_code == status.HTTP_400_BAD_REQUEST

    # 3. Accept verification with valid HMAC signature
    payment_id = "pay_mock_valid_99999"
    msg = f"{provider_order_id}|{payment_id}".encode()
    valid_sig = hmac.new(MockPaymentProvider.MOCK_SECRET.encode("utf-8"), msg, hashlib.sha256).hexdigest()

    good_verify_payload = {
        "provider_order_id": provider_order_id,
        "provider_payment_id": payment_id,
        "signature": valid_sig,
        "payment_method": "upi",
    }
    good_resp = client.post("/api/v1/payments/verify", good_verify_payload, format="json")
    assert good_resp.status_code == status.HTTP_200_OK
    assert good_resp.json()["status"] == "success"

    order = PaymentOrder.objects.get(provider_order_id=provider_order_id)
    assert order.status == PaymentOrder.STATUS_PAID


@pytest.mark.django_db
def test_online_payment_refund_flow(finance_setup: dict) -> None:
    """Admin can issue full or partial refund against a successful payment transaction."""
    resident = finance_setup["resident"]
    admin = finance_setup["admin"]
    booking = finance_setup["booking"]

    client_res = APIClient()
    client_res.force_authenticate(user=resident)

    # Create and verify order
    order_resp = client_res.post("/api/v1/payments/orders", {"booking_id": str(booking.id)}, format="json")
    provider_order_id = order_resp.json()["provider_order_id"]

    client_res.post(
        "/api/v1/payments/verify",
        {
            "provider_order_id": provider_order_id,
            "provider_payment_id": "pay_mock_refund_1",
            "signature": "valid_mock_signature",
        },
        format="json",
    )

    order = PaymentOrder.objects.get(provider_order_id=provider_order_id)
    txn = order.transactions.get(status=PaymentTransaction.STATUS_SUCCESS)

    # Admin issues refund
    client_admin = APIClient()
    client_admin.force_authenticate(user=admin)
    refund_resp = client_admin.post(
        f"/api/v1/payments/transactions/{txn.id}/refund",
        {"amount_minor_units": txn.amount_minor_units, "reason": "Service cancelled amicably"},
        format="json",
    )
    assert refund_resp.status_code == status.HTTP_201_CREATED
    assert refund_resp.json()["status"] == "processed"

    txn.refresh_from_db()
    assert txn.status == PaymentTransaction.STATUS_REFUNDED


@pytest.mark.django_db
def test_cash_on_delivery_reporting_and_confirmation(finance_setup: dict) -> None:
    """Cook reports cash collection, platform commission is accrued, and household confirms receipt."""
    cook = finance_setup["cook"]
    resident = finance_setup["resident"]
    booking = finance_setup["booking"]

    # 1. Cook reports cash collected
    client_cook = APIClient()
    client_cook.force_authenticate(user=cook.user)

    cash_payload = {
        "reported_amount_minor_units": booking.price_breakdown.total_amount_minor_units,
        "cook_notes": "Received exact cash 290 INR from resident.",
    }
    report_resp = client_cook.post(
        f"/api/v1/cooks/visits/{booking.id}/cash-collection",
        cash_payload,
        format="json",
    )
    assert report_resp.status_code == status.HTTP_201_CREATED
    cash_record = CashCollectionRecord.objects.get(booking=booking)
    assert cash_record.status == CashCollectionRecord.STATUS_REPORTED

    # Verify commission liability accrued in ledger
    ledger_entry = CommissionLedger.objects.filter(cook=cook, booking=booking).first()
    assert ledger_entry is not None
    assert ledger_entry.entry_type == CommissionLedger.TYPE_COMMISSION_ACCRUED
    assert ledger_entry.amount_minor_units == booking.price_breakdown.platform_commission_minor_units
    assert ledger_entry.running_balance_minor_units > 0

    # 2. Household confirms cash payment
    client_res = APIClient()
    client_res.force_authenticate(user=resident)
    confirm_resp = client_res.post(f"/api/v1/households/visits/{booking.id}/confirm-cash")
    assert confirm_resp.status_code == status.HTTP_200_OK
    cash_record.refresh_from_db()
    assert cash_record.status == CashCollectionRecord.STATUS_CONFIRMED


@pytest.mark.django_db
def test_cash_dispute_and_admin_arbitration(finance_setup: dict) -> None:
    """Household disputes cash collection, and admin arbitrates final amount."""
    cook = finance_setup["cook"]
    resident = finance_setup["resident"]
    admin = finance_setup["admin"]
    booking = finance_setup["booking"]

    # 1. Cook reports cash
    client_cook = APIClient()
    client_cook.force_authenticate(user=cook.user)
    client_cook.post(
        f"/api/v1/cooks/visits/{booking.id}/cash-collection",
        {"reported_amount_minor_units": 50000},
        format="json",
    )
    cash_record = CashCollectionRecord.objects.get(booking=booking)

    # 2. Household disputes amount
    client_res = APIClient()
    client_res.force_authenticate(user=resident)
    dispute_resp = client_res.post(
        f"/api/v1/households/visits/{booking.id}/dispute-cash",
        {"dispute_reason": "I only paid 300 INR, not 500 INR."},
        format="json",
    )
    assert dispute_resp.status_code == status.HTTP_200_OK
    cash_record.refresh_from_db()
    assert cash_record.status == CashCollectionRecord.STATUS_DISPUTED

    # 3. Admin arbitrates dispute
    client_admin = APIClient()
    client_admin.force_authenticate(user=admin)
    resolve_resp = client_admin.post(
        f"/api/v1/admin/cash-collections/{cash_record.id}/resolve",
        {"resolved_amount_minor_units": 30000, "resolution_notes": "Resident receipt verified for 300 INR."},
        format="json",
    )
    assert resolve_resp.status_code == status.HTTP_200_OK
    cash_record.refresh_from_db()
    assert cash_record.status == CashCollectionRecord.STATUS_RESOLVED
    assert cash_record.reported_amount_minor_units == 30000


@pytest.mark.django_db
def test_cook_earnings_summary_and_payout_deduction(finance_setup: dict) -> None:
    """Verify cook financial summary and commission liability deduction during payout."""
    cook = finance_setup["cook"]
    admin = finance_setup["admin"]
    booking = finance_setup["booking"]
    assignment = finance_setup["assignment"]

    # Mark visit completed
    assignment.status = CookAssignment.STATUS_COMPLETED
    assignment.save()

    # Online payment processed for booking
    order = PaymentOrder.objects.create(
        household=booking.household,
        booking=booking,
        amount_minor_units=booking.price_breakdown.total_amount_minor_units,
        provider_order_id="order_payout_test_1",
        status=PaymentOrder.STATUS_PAID,
    )
    PaymentTransaction.objects.create(
        payment_order=order,
        provider_payment_id="pay_payout_test_1",
        amount_minor_units=order.amount_minor_units,
        status=PaymentTransaction.STATUS_SUCCESS,
    )

    # Cook also has an outstanding cash commission liability of 1000 paise
    CommissionLedger.objects.create(
        cook=cook,
        entry_type=CommissionLedger.TYPE_COMMISSION_ACCRUED,
        amount_minor_units=1000,
        running_balance_minor_units=1000,
        description="Prior COD commission liability",
    )

    # 1. Cook views financial summary
    client_cook = APIClient()
    client_cook.force_authenticate(user=cook.user)
    summary_resp = client_cook.get("/api/v1/cooks/me/earnings")
    assert summary_resp.status_code == status.HTTP_200_OK
    data = summary_resp.json()
    assert data["gross_online_earnings_minor_units"] == booking.price_breakdown.cook_earnings_minor_units
    assert data["outstanding_commission_liability_minor_units"] == 1000
    assert data["net_payable_minor_units"] == data["gross_online_earnings_minor_units"] - 1000

    # 2. Admin processes payout
    client_admin = APIClient()
    client_admin.force_authenticate(user=admin)
    payout_payload = {
        "cook_id": str(cook.id),
        "period_start": "2027-02-01",
        "period_end": "2027-02-28",
    }
    payout_resp = client_admin.post("/api/v1/admin/finance/payouts", payout_payload, format="json")
    assert payout_resp.status_code == status.HTTP_201_CREATED
    payout_data = payout_resp.json()
    assert payout_data["status"] == "processed"
    assert payout_data["commission_deductions_minor_units"] == 1000
    assert payout_data["net_payout_amount_minor_units"] == data["net_payable_minor_units"]
