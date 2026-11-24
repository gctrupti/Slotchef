"""Cook earnings reconciliation, commission deduction, and payout batching service."""

from __future__ import annotations

import datetime
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from apps.audit.models import AuditLog
from apps.cooks.models import CookProfile
from apps.finance.models import (
    CashCollectionRecord,
    CommissionLedger,
    CookPayoutRecord,
    PaymentOrder,
)
from apps.identity.models import User
from apps.scheduling.models import CookAssignment


class PayoutService:
    """Calculates cook net balances and processes payout disbursements."""

    @classmethod
    def get_cook_financial_summary(cls, cook: CookProfile) -> dict[str, Any]:
        """Aggregate gross earnings, cash collections, and outstanding commission liabilities."""
        # 1. Gross online earnings from completed visits where online payment succeeded
        completed_assignments = CookAssignment.objects.filter(
            cook=cook,
            status=CookAssignment.STATUS_COMPLETED,
        ).values_list("booking_id", flat=True)

        paid_bookings = PaymentOrder.objects.filter(
            booking_id__in=completed_assignments,
            status=PaymentOrder.STATUS_PAID,
        ).values_list("booking_id", flat=True)

        gross_online = 0
        from apps.finance.models import BookingPriceBreakdown
        breakdowns = BookingPriceBreakdown.objects.filter(booking_id__in=paid_bookings)
        for bd in breakdowns:
            gross_online += bd.cook_earnings_minor_units

        # 2. Total cash collected by cook directly from households
        cash_records = CashCollectionRecord.objects.filter(
            cook=cook,
            status__in=[CashCollectionRecord.STATUS_CONFIRMED, CashCollectionRecord.STATUS_RESOLVED],
        )
        total_cash = cash_records.aggregate(total=models.Sum("reported_amount_minor_units"))["total"] or 0

        # 3. Outstanding commission balance owed to platform
        latest_ledger = CommissionLedger.objects.filter(cook=cook).order_by("-created_at").first()
        commission_liability = latest_ledger.running_balance_minor_units if latest_ledger else 0

        # 4. Net payable = online earnings minus outstanding commission liability
        net_payable = max(0, gross_online - commission_liability)

        return {
            "cook_id": str(cook.id),
            "cook_email": cook.user.email,
            "gross_online_earnings_minor_units": gross_online,
            "total_cash_collected_minor_units": total_cash,
            "outstanding_commission_liability_minor_units": commission_liability,
            "net_payable_minor_units": net_payable,
            "currency": "INR",
        }

    @classmethod
    def process_cook_payout(
        cls,
        cook: CookProfile,
        period_start: datetime.date,
        period_end: datetime.date,
        actor: User | None = None,
    ) -> CookPayoutRecord:
        """Disburse net payable earnings to cook, offsetting outstanding commission liability."""
        summary = cls.get_cook_financial_summary(cook)
        net_payable = summary["net_payable_minor_units"]
        gross_online = summary["gross_online_earnings_minor_units"]
        commission_owed = summary["outstanding_commission_liability_minor_units"]

        if net_payable <= 0 and gross_online <= 0:
            raise ValidationError("No payable earnings available for disbursement.")

        with transaction.atomic():
            now = timezone.now()
            payout = CookPayoutRecord.objects.create(
                cook=cook,
                period_start=period_start,
                period_end=period_end,
                gross_online_earnings_minor_units=gross_online,
                commission_deductions_minor_units=min(gross_online, commission_owed),
                net_payout_amount_minor_units=net_payable,
                currency="INR",
                status=CookPayoutRecord.STATUS_PROCESSED,
                reference_id=f"PAYOUT_{cook.id.hex[:8]}_{now.strftime('%Y%m%d%H%M')}",
                processed_at=now,
            )

            # Offset commission ledger
            deduction = min(gross_online, commission_owed)
            if deduction > 0:
                new_bal = commission_owed - deduction
                CommissionLedger.objects.create(
                    cook=cook,
                    entry_type=CommissionLedger.TYPE_COMMISSION_DEDUCTED,
                    amount_minor_units=deduction,
                    running_balance_minor_units=new_bal,
                    description=f"Commission offset against Payout {payout.reference_id}",
                )

            AuditLog.objects.create(
                actor=actor,
                action="COOK_PAYOUT_PROCESSED",
                entity_type="CookPayoutRecord",
                entity_id=str(payout.id),
                after_state={
                    "reference": payout.reference_id,
                    "net_amount": net_payable,
                    "commission_deducted": deduction,
                },
            )

        return payout

