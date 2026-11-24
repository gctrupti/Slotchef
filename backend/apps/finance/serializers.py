"""Serializers for Finance and Pricing domain."""

from __future__ import annotations

from rest_framework import serializers

from apps.bookings.models import Booking
from apps.finance.models import (
    BookingPriceBreakdown,
    CashCollectionRecord,
    CommissionLedger,
    CookPayoutRecord,
    PaymentOrder,
    PaymentTransaction,
    PlatformCommissionConfig,
    RefundRecord,
    ServicePricingRule,
)


class ServicePricingRuleSerializer(serializers.ModelSerializer):
    """Serializer for service pricing rules."""

    society_name = serializers.CharField(source="society.name", read_only=True)

    class Meta:
        model = ServicePricingRule
        fields = [
            "id",
            "society",
            "society_name",
            "name",
            "code",
            "pricing_type",
            "base_fee_minor_units",
            "per_minute_rate_minor_units",
            "breakfast_multiplier",
            "lunch_multiplier",
            "dinner_multiplier",
            "snacks_multiplier",
            "currency",
            "is_active",
            "effective_from",
            "effective_to",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_code(self, value: str) -> str:
        return value.strip().upper()


class PlatformCommissionConfigSerializer(serializers.ModelSerializer):
    """Serializer for platform commission configuration."""

    society_name = serializers.CharField(source="society.name", read_only=True)

    class Meta:
        model = PlatformCommissionConfig
        fields = [
            "id",
            "society",
            "society_name",
            "commission_type",
            "percentage_rate",
            "fixed_fee_minor_units",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class BookingPriceBreakdownSerializer(serializers.ModelSerializer):
    """Detailed price breakdown serializer with snapshot metadata."""

    class Meta:
        model = BookingPriceBreakdown
        fields = [
            "id",
            "booking",
            "pricing_rule",
            "commission_config",
            "base_fee_minor_units",
            "duration_fee_minor_units",
            "meal_multiplier",
            "subtotal_minor_units",
            "platform_commission_minor_units",
            "cook_earnings_minor_units",
            "tax_minor_units",
            "discount_minor_units",
            "total_amount_minor_units",
            "currency",
            "snapshot_metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class PriceEstimateRequestSerializer(serializers.Serializer):
    """Request payload to calculate an upfront price estimate."""

    society_id = serializers.UUIDField(required=False, allow_null=True)
    duration_minutes = serializers.IntegerField(default=45, min_value=15, max_value=240)
    meal_type = serializers.ChoiceField(choices=Booking.MEAL_CHOICES, default=Booking.MEAL_BREAKFAST)
    pricing_type = serializers.ChoiceField(
        choices=ServicePricingRule.TYPE_CHOICES,
        default=ServicePricingRule.TYPE_PER_VISIT,
    )


class PriceEstimateResponseSerializer(serializers.Serializer):
    """Response format for estimated pricing breakdown."""

    duration_minutes = serializers.IntegerField()
    meal_type = serializers.CharField()
    base_fee_minor_units = serializers.IntegerField()
    duration_fee_minor_units = serializers.IntegerField()
    meal_multiplier = serializers.FloatField()
    subtotal_minor_units = serializers.IntegerField()
    platform_commission_minor_units = serializers.IntegerField()
    cook_earnings_minor_units = serializers.IntegerField()
    total_amount_minor_units = serializers.IntegerField()
    currency = serializers.CharField()
    rule_code = serializers.CharField()
    commission_rate = serializers.FloatField()


# ==============================================================================
# Phase 10 Serializers: Online Payments, Cash on Delivery, Commission, Payouts
# ==============================================================================

class PaymentOrderSerializer(serializers.ModelSerializer):
    """Payment order serializer."""

    class Meta:
        model = PaymentOrder
        fields = [
            "id",
            "household",
            "booking",
            "subscription",
            "amount_minor_units",
            "currency",
            "provider",
            "provider_order_id",
            "status",
            "idempotency_key",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class PaymentOrderCreateRequestSerializer(serializers.Serializer):
    """Payload to create an online payment order."""

    booking_id = serializers.UUIDField(required=False, allow_null=True)
    subscription_id = serializers.UUIDField(required=False, allow_null=True)
    idempotency_key = serializers.CharField(required=False, allow_blank=True, default="")


class PaymentVerifyRequestSerializer(serializers.Serializer):
    """Payload to verify gateway payment signature."""

    provider_order_id = serializers.CharField()
    provider_payment_id = serializers.CharField()
    signature = serializers.CharField()
    payment_method = serializers.CharField(default="card")


class PaymentTransactionSerializer(serializers.ModelSerializer):
    """Payment transaction details."""

    class Meta:
        model = PaymentTransaction
        fields = [
            "id",
            "payment_order",
            "provider_payment_id",
            "amount_minor_units",
            "status",
            "payment_method",
            "signature",
            "error_code",
            "error_description",
            "created_at",
        ]
        read_only_fields = fields


class RefundRequestSerializer(serializers.Serializer):
    """Payload to issue a refund."""

    amount_minor_units = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    reason = serializers.CharField(required=False, allow_blank=True, default="")


class RefundRecordSerializer(serializers.ModelSerializer):
    """Refund record serializer."""

    class Meta:
        model = RefundRecord
        fields = [
            "id",
            "payment_transaction",
            "amount_minor_units",
            "reason",
            "provider_refund_id",
            "status",
            "created_at",
        ]
        read_only_fields = fields


class CashCollectionRecordSerializer(serializers.ModelSerializer):
    """Cash on delivery visit collection record."""

    cook_email = serializers.CharField(source="cook.user.email", read_only=True)

    class Meta:
        model = CashCollectionRecord
        fields = [
            "id",
            "booking",
            "cook",
            "cook_email",
            "household",
            "reported_amount_minor_units",
            "collected_at",
            "status",
            "cook_notes",
            "household_dispute_reason",
            "admin_resolution_notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CashReportRequestSerializer(serializers.Serializer):
    """Cook reporting physical cash collection."""

    reported_amount_minor_units = serializers.IntegerField(min_value=1)
    cook_notes = serializers.CharField(required=False, allow_blank=True, default="")


class CashDisputeRequestSerializer(serializers.Serializer):
    """Household disputing physical cash collection."""

    dispute_reason = serializers.CharField(min_length=5)


class CashResolveRequestSerializer(serializers.Serializer):
    """Admin resolving cash collection dispute."""

    resolved_amount_minor_units = serializers.IntegerField(min_value=0)
    resolution_notes = serializers.CharField(min_length=5)


class CommissionLedgerSerializer(serializers.ModelSerializer):
    """Cook commission ledger entry."""

    cook_email = serializers.CharField(source="cook.user.email", read_only=True)

    class Meta:
        model = CommissionLedger
        fields = [
            "id",
            "cook",
            "cook_email",
            "booking",
            "entry_type",
            "amount_minor_units",
            "running_balance_minor_units",
            "description",
            "created_at",
        ]
        read_only_fields = fields


class CookFinancialSummarySerializer(serializers.Serializer):
    """Summary of cook gross earnings, cash collections, and payable net balance."""

    cook_id = serializers.CharField()
    cook_email = serializers.CharField()
    gross_online_earnings_minor_units = serializers.IntegerField()
    total_cash_collected_minor_units = serializers.IntegerField()
    outstanding_commission_liability_minor_units = serializers.IntegerField()
    net_payable_minor_units = serializers.IntegerField()
    currency = serializers.CharField()


class CookPayoutRecordSerializer(serializers.ModelSerializer):
    """Cook payout disbursement record."""

    cook_email = serializers.CharField(source="cook.user.email", read_only=True)

    class Meta:
        model = CookPayoutRecord
        fields = [
            "id",
            "cook",
            "cook_email",
            "period_start",
            "period_end",
            "gross_online_earnings_minor_units",
            "commission_deductions_minor_units",
            "net_payout_amount_minor_units",
            "currency",
            "status",
            "reference_id",
            "created_at",
            "processed_at",
        ]
        read_only_fields = fields


class CookPayoutCreateRequestSerializer(serializers.Serializer):
    """Admin payload to trigger cook payout disbursement."""

    cook_id = serializers.UUIDField()
    period_start = serializers.DateField()
    period_end = serializers.DateField()


