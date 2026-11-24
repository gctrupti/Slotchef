"""URL routes for Finance and Pricing endpoints."""

from __future__ import annotations

from django.urls import path

from apps.finance.views import (
    AdminCashResolveView,
    AdminCommissionLedgerListView,
    AdminCookPayoutCreateView,
    BookingPriceBreakdownDetailView,
    CookCashReportView,
    CookEarningsSummaryView,
    HouseholdCashConfirmView,
    HouseholdCashDisputeView,
    PaymentHistoryView,
    PaymentOrderCreateView,
    PaymentRefundView,
    PaymentVerifyView,
    PaymentWebhookView,
    PlatformCommissionConfigView,
    PriceEstimateView,
    ServicePricingRuleDetailView,
    ServicePricingRuleListCreateView,
)

urlpatterns = [
    # Public & Resident Pricing inspection & estimation
    path("pricing/rules", ServicePricingRuleListCreateView.as_view(), name="pricing-rule-list-create"),
    path("pricing/rules/<uuid:rule_id>", ServicePricingRuleDetailView.as_view(), name="pricing-rule-detail"),
    path("pricing/estimate", PriceEstimateView.as_view(), name="pricing-estimate"),

    # Admin Commission controls
    path("admin/pricing/commission", PlatformCommissionConfigView.as_view(), name="admin-commission-config"),

    # Booking price snapshot
    path("bookings/<uuid:booking_id>/price-breakdown", BookingPriceBreakdownDetailView.as_view(), name="booking-price-breakdown"),

    # Phase 10: Online Payments
    path("payments/orders", PaymentOrderCreateView.as_view(), name="payment-order-create"),
    path("payments/verify", PaymentVerifyView.as_view(), name="payment-verify"),
    path("payments/webhook", PaymentWebhookView.as_view(), name="payment-webhook"),
    path("payments/transactions/<uuid:transaction_id>/refund", PaymentRefundView.as_view(), name="payment-refund"),
    path("payments/history", PaymentHistoryView.as_view(), name="payment-history"),

    # Phase 10: Cash on Delivery & Disputes
    path("cooks/visits/<uuid:booking_id>/cash-collection", CookCashReportView.as_view(), name="cook-cash-report"),
    path("households/visits/<uuid:booking_id>/confirm-cash", HouseholdCashConfirmView.as_view(), name="household-cash-confirm"),
    path("households/visits/<uuid:booking_id>/dispute-cash", HouseholdCashDisputeView.as_view(), name="household-cash-dispute"),
    path("admin/cash-collections/<uuid:cash_record_id>/resolve", AdminCashResolveView.as_view(), name="admin-cash-resolve"),

    # Phase 10: Cook Financial Summary & Payouts
    path("cooks/me/earnings", CookEarningsSummaryView.as_view(), name="cook-earnings-summary"),
    path("admin/finance/ledger", AdminCommissionLedgerListView.as_view(), name="admin-commission-ledger"),
    path("admin/finance/payouts", AdminCookPayoutCreateView.as_view(), name="admin-cook-payouts"),
]

