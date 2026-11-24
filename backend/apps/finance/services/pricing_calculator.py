"""Service pricing, commission, and price breakdown calculation engine."""

from __future__ import annotations

import decimal
from typing import Any

from django.db import transaction

from apps.bookings.models import Booking
from apps.communities.models import Society
from apps.finance.models import (
    BookingPriceBreakdown,
    PlatformCommissionConfig,
    ServicePricingRule,
)


class PricingCalculatorService:
    """Calculates, validates, and snapshots service pricing and platform commission."""

    DEFAULT_BASE_FEE_PAISE = 20000  # 200.00 INR
    DEFAULT_PER_MINUTE_PAISE = 250  # 2.50 INR / min
    DEFAULT_COMMISSION_PCT = decimal.Decimal("15.00")

    @classmethod
    def get_effective_pricing_rule(
        cls,
        society: Society | None,
        pricing_type: str = ServicePricingRule.TYPE_PER_VISIT,
    ) -> ServicePricingRule | None:
        """Find active society override rule or global fallback."""
        if society:
            rule = ServicePricingRule.objects.filter(
                society=society,
                pricing_type=pricing_type,
                is_active=True,
            ).first()
            if rule:
                return rule

        return ServicePricingRule.objects.filter(
            society__isnull=True,
            pricing_type=pricing_type,
            is_active=True,
        ).first()

    @classmethod
    def get_effective_commission_config(
        cls,
        society: Society | None,
    ) -> PlatformCommissionConfig | None:
        """Find active society override commission config or global fallback."""
        if society:
            cfg = PlatformCommissionConfig.objects.filter(
                society=society,
                is_active=True,
            ).first()
            if cfg:
                return cfg

        return PlatformCommissionConfig.objects.filter(
            society__isnull=True,
            is_active=True,
        ).first()

    @classmethod
    def calculate_price_breakdown(
        cls,
        booking: Booking,
        pricing_rule: ServicePricingRule | None = None,
        commission_config: PlatformCommissionConfig | None = None,
        persist: bool = True,
    ) -> BookingPriceBreakdown:
        """Compute exact itemized price breakdown and save immutable historical snapshot."""
        society = getattr(booking.household, "society", None)

        rule = pricing_rule or cls.get_effective_pricing_rule(society)
        cfg = commission_config or cls.get_effective_commission_config(society)

        duration = max(1, booking.duration_minutes)
        meal_type = getattr(booking, "meal_type", Booking.MEAL_BREAKFAST)

        base_fee = int(rule.base_fee_minor_units) if rule else cls.DEFAULT_BASE_FEE_PAISE
        per_minute = int(rule.per_minute_rate_minor_units) if rule else cls.DEFAULT_PER_MINUTE_PAISE
        currency = rule.currency if rule else "INR"

        duration_fee = duration * per_minute
        raw_amount = base_fee + duration_fee

        meal_mult = rule.get_meal_multiplier(meal_type) if rule else 1.0
        subtotal = int(round(raw_amount * meal_mult))

        if cfg:
            commission = cfg.calculate_commission(subtotal)
        else:
            commission = int(round(subtotal * (float(cls.DEFAULT_COMMISSION_PCT) / 100.0)))

        cook_earnings = max(0, subtotal - commission)
        tax = 0
        discount = 0
        total_amount = subtotal + tax - discount

        snapshot_metadata: dict[str, Any] = {
            "duration_minutes": duration,
            "meal_type": meal_type,
            "base_fee_minor_units": base_fee,
            "per_minute_rate_minor_units": per_minute,
            "meal_multiplier": float(meal_mult),
            "raw_sum_minor_units": raw_amount,
            "subtotal_minor_units": subtotal,
            "commission_type": cfg.commission_type if cfg else "default_percentage",
            "commission_rate": float(cfg.percentage_rate) if cfg else float(cls.DEFAULT_COMMISSION_PCT),
            "platform_commission_minor_units": commission,
            "cook_earnings_minor_units": cook_earnings,
            "currency": currency,
            "rule_id": str(rule.id) if rule else None,
            "rule_code": rule.code if rule else "DEFAULT_FALLBACK",
            "commission_config_id": str(cfg.id) if cfg else None,
        }

        breakdown_defaults = {
            "pricing_rule": rule,
            "commission_config": cfg,
            "base_fee_minor_units": base_fee,
            "duration_fee_minor_units": duration_fee,
            "meal_multiplier": decimal.Decimal(str(round(meal_mult, 2))),
            "subtotal_minor_units": subtotal,
            "platform_commission_minor_units": commission,
            "cook_earnings_minor_units": cook_earnings,
            "tax_minor_units": tax,
            "discount_minor_units": discount,
            "total_amount_minor_units": total_amount,
            "currency": currency,
            "snapshot_metadata": snapshot_metadata,
        }

        if persist:
            with transaction.atomic():
                breakdown, _ = BookingPriceBreakdown.objects.update_or_create(
                    booking=booking,
                    defaults=breakdown_defaults,
                )
                return breakdown
        else:
            return BookingPriceBreakdown(booking=booking, **breakdown_defaults)

    @classmethod
    def estimate_price(
        cls,
        society: Society | None,
        duration_minutes: int,
        meal_type: str = Booking.MEAL_BREAKFAST,
        pricing_type: str = ServicePricingRule.TYPE_PER_VISIT,
    ) -> dict[str, Any]:
        """Estimate price breakdown for a hypothetical service request without a booking record."""
        rule = cls.get_effective_pricing_rule(society, pricing_type)
        cfg = cls.get_effective_commission_config(society)

        duration = max(1, duration_minutes)
        base_fee = int(rule.base_fee_minor_units) if rule else cls.DEFAULT_BASE_FEE_PAISE
        per_minute = int(rule.per_minute_rate_minor_units) if rule else cls.DEFAULT_PER_MINUTE_PAISE
        currency = rule.currency if rule else "INR"

        duration_fee = duration * per_minute
        raw_amount = base_fee + duration_fee

        meal_mult = rule.get_meal_multiplier(meal_type) if rule else 1.0
        subtotal = int(round(raw_amount * meal_mult))

        if cfg:
            commission = cfg.calculate_commission(subtotal)
        else:
            commission = int(round(subtotal * (float(cls.DEFAULT_COMMISSION_PCT) / 100.0)))

        cook_earnings = max(0, subtotal - commission)
        total_amount = subtotal

        return {
            "duration_minutes": duration,
            "meal_type": meal_type,
            "base_fee_minor_units": base_fee,
            "duration_fee_minor_units": duration_fee,
            "meal_multiplier": float(meal_mult),
            "subtotal_minor_units": subtotal,
            "platform_commission_minor_units": commission,
            "cook_earnings_minor_units": cook_earnings,
            "total_amount_minor_units": total_amount,
            "currency": currency,
            "rule_code": rule.code if rule else "DEFAULT_FALLBACK",
            "commission_rate": float(cfg.percentage_rate) if cfg else float(cls.DEFAULT_COMMISSION_PCT),
        }

