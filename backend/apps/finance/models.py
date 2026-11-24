"""Finance schema baseline models (integers for minor units, payment gateways deferred)."""

from __future__ import annotations

import uuid

from django.db import models

from apps.bookings.models import Booking, HouseholdPackageSubscription
from apps.communities.models import Society
from apps.cooks.models import CookProfile
from apps.households.models import Household


class Invoice(models.Model):
    """Monthly or per-visit invoice for household cooking visits."""

    STATUS_DRAFT = "draft"
    STATUS_ISSUED = "issued"
    STATUS_PAID = "paid"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = (
        (STATUS_DRAFT, "Draft"),
        (STATUS_ISSUED, "Issued"),
        (STATUS_PAID, "Paid"),
        (STATUS_CANCELLED, "Cancelled"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    household = models.ForeignKey(Household, on_delete=models.PROTECT, related_name="invoices")
    total_amount_minor_units = models.BigIntegerField(default=0, help_text="Total in minor units (e.g. cents/paise)")
    currency = models.CharField(max_length=3, default="USD")
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    period_start = models.DateField()
    period_end = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "finance_invoice"


class PaymentRecord(models.Model):
    """Simulated or ledger-recorded payment transaction."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="payments")
    amount_minor_units = models.BigIntegerField()
    currency = models.CharField(max_length=3, default="USD")
    payment_method = models.CharField(max_length=64, default="simulated")
    reference = models.CharField(max_length=128, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "finance_payment_record"


class LedgerEntry(models.Model):
    """Double-entry style financial record for billing audit."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name="ledger_entries")
    account_code = models.CharField(max_length=64)
    amount_minor_units = models.BigIntegerField()
    currency = models.CharField(max_length=3, default="USD")
    description = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "finance_ledger_entry"


class ServicePricingRule(models.Model):
    """Configurable service pricing rules for per-visit, weekly, and monthly calculations."""

    TYPE_PER_VISIT = "per_visit"
    TYPE_WEEKLY_PLAN = "weekly_plan"
    TYPE_MONTHLY_PLAN = "monthly_plan"

    TYPE_CHOICES = (
        (TYPE_PER_VISIT, "Per-Visit Pricing"),
        (TYPE_WEEKLY_PLAN, "Weekly Subscription Base"),
        (TYPE_MONTHLY_PLAN, "Monthly Subscription Base"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    society = models.ForeignKey(
        Society,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="pricing_rules",
        help_text="Society-specific override; null indicates global platform baseline.",
    )
    name = models.CharField(max_length=128)
    code = models.CharField(max_length=64, db_index=True)
    pricing_type = models.CharField(max_length=32, choices=TYPE_CHOICES, default=TYPE_PER_VISIT)
    base_fee_minor_units = models.BigIntegerField(
        default=20000,
        help_text="Fixed base visit fee in minor currency units (e.g., 20000 paise = 200 INR).",
    )
    per_minute_rate_minor_units = models.BigIntegerField(
        default=250,
        help_text="Rate per service minute in minor units (e.g., 250 paise = 2.5 INR/min).",
    )
    breakfast_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1.00)
    lunch_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1.20)
    dinner_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1.25)
    snacks_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=0.90)
    currency = models.CharField(max_length=3, default="INR")
    is_active = models.BooleanField(default=True, db_index=True)
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "finance_service_pricing_rule"
        ordering = ["-is_active", "society", "name"]
        indexes = [
            models.Index(fields=["code", "is_active"], name="idx_pricing_code_active"),
        ]

    def __str__(self) -> str:
        soc = self.society.name if self.society else "Global"
        return f"PricingRule: {self.name} [{soc}] ({self.pricing_type})"

    def get_meal_multiplier(self, meal_type: str) -> float:
        mapping = {
            "breakfast": float(self.breakfast_multiplier),
            "lunch": float(self.lunch_multiplier),
            "dinner": float(self.dinner_multiplier),
            "snacks": float(self.snacks_multiplier),
        }
        return mapping.get(meal_type.lower(), 1.0)


class PlatformCommissionConfig(models.Model):
    """Configurable platform commission policy."""

    TYPE_PERCENTAGE = "percentage"
    TYPE_FIXED = "fixed"
    TYPE_HYBRID = "hybrid"

    TYPE_CHOICES = (
        (TYPE_PERCENTAGE, "Percentage of Subtotal"),
        (TYPE_FIXED, "Fixed Fee Per Visit"),
        (TYPE_HYBRID, "Hybrid (Percentage + Fixed Fee)"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    society = models.ForeignKey(
        Society,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="commission_configs",
        help_text="Society-specific commission override; null indicates global default.",
    )
    commission_type = models.CharField(max_length=32, choices=TYPE_CHOICES, default=TYPE_PERCENTAGE)
    percentage_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=15.00,
        help_text="Platform commission percentage (e.g. 15.00%).",
    )
    fixed_fee_minor_units = models.BigIntegerField(
        default=0,
        help_text="Fixed commission fee per visit in minor units (paise).",
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "finance_commission_config"
        ordering = ["-is_active", "society"]

    def __str__(self) -> str:
        soc = self.society.name if self.society else "Global"
        return f"CommissionConfig [{soc}] ({self.commission_type}): {self.percentage_rate}%"

    def calculate_commission(self, subtotal_minor_units: int) -> int:
        """Compute commission amount in minor units."""
        rate = float(self.percentage_rate) / 100.0
        pct_amount = int(round(subtotal_minor_units * rate))
        if self.commission_type == self.TYPE_PERCENTAGE:
            return pct_amount
        if self.commission_type == self.TYPE_FIXED:
            return int(self.fixed_fee_minor_units)
        return pct_amount + int(self.fixed_fee_minor_units)


class BookingPriceBreakdown(models.Model):
    """Historical price snapshot and breakdown for a confirmed booking."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name="price_breakdown",
    )
    pricing_rule = models.ForeignKey(
        ServicePricingRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="applied_breakdowns",
    )
    commission_config = models.ForeignKey(
        PlatformCommissionConfig,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="applied_breakdowns",
    )
    base_fee_minor_units = models.BigIntegerField()
    duration_fee_minor_units = models.BigIntegerField()
    meal_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1.00)
    subtotal_minor_units = models.BigIntegerField()
    platform_commission_minor_units = models.BigIntegerField()
    cook_earnings_minor_units = models.BigIntegerField()
    tax_minor_units = models.BigIntegerField(default=0)
    discount_minor_units = models.BigIntegerField(default=0)
    total_amount_minor_units = models.BigIntegerField()
    currency = models.CharField(max_length=3, default="INR")
    snapshot_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Immutable audit snapshot of multipliers and formula inputs at calculation time.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "finance_booking_price_breakdown"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return (
            f"PriceBreakdown for Booking {self.booking_id}: Total {self.total_amount_minor_units} {self.currency} "
            f"(Cook: {self.cook_earnings_minor_units}, Platform: {self.platform_commission_minor_units})"
        )


class PaymentOrder(models.Model):
    """Online payment order initiated through a payment provider."""

    STATUS_CREATED = "created"
    STATUS_PAID = "paid"
    STATUS_FAILED = "failed"
    STATUS_EXPIRED = "expired"

    STATUS_CHOICES = (
        (STATUS_CREATED, "Created"),
        (STATUS_PAID, "Paid"),
        (STATUS_FAILED, "Failed"),
        (STATUS_EXPIRED, "Expired"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    household = models.ForeignKey(Household, on_delete=models.PROTECT, related_name="payment_orders")
    booking = models.ForeignKey(
        Booking,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="payment_orders",
    )
    subscription = models.ForeignKey(
        HouseholdPackageSubscription,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="payment_orders",
    )
    amount_minor_units = models.BigIntegerField()
    currency = models.CharField(max_length=3, default="INR")
    provider = models.CharField(max_length=64, default="mock")
    provider_order_id = models.CharField(max_length=128, unique=True, db_index=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_CREATED, db_index=True)
    idempotency_key = models.CharField(max_length=128, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "finance_payment_order"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"PaymentOrder {self.provider_order_id} [{self.status}] ({self.amount_minor_units} {self.currency})"


class PaymentTransaction(models.Model):
    """Completed or attempted online transaction record with verification proof."""

    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUS_REFUNDED = "refunded"

    STATUS_CHOICES = (
        (STATUS_SUCCESS, "Success"),
        (STATUS_FAILED, "Failed"),
        (STATUS_REFUNDED, "Refunded"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment_order = models.ForeignKey(PaymentOrder, on_delete=models.CASCADE, related_name="transactions")
    provider_payment_id = models.CharField(max_length=128, db_index=True)
    amount_minor_units = models.BigIntegerField()
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_SUCCESS, db_index=True)
    payment_method = models.CharField(max_length=64, default="card")
    signature = models.CharField(max_length=255, blank=True, default="")
    error_code = models.CharField(max_length=64, blank=True, default="")
    error_description = models.TextField(blank=True, default="")
    raw_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "finance_payment_transaction"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Transaction {self.provider_payment_id} [{self.status}] - {self.amount_minor_units}"


class RefundRecord(models.Model):
    """Record of full or partial refund issued against an online transaction."""

    STATUS_REQUESTED = "requested"
    STATUS_PROCESSED = "processed"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = (
        (STATUS_REQUESTED, "Requested"),
        (STATUS_PROCESSED, "Processed"),
        (STATUS_FAILED, "Failed"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment_transaction = models.ForeignKey(PaymentTransaction, on_delete=models.PROTECT, related_name="refunds")
    amount_minor_units = models.BigIntegerField()
    reason = models.TextField(blank=True, default="")
    provider_refund_id = models.CharField(max_length=128, blank=True, default="")
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_PROCESSED, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "finance_refund_record"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Refund {self.id} for Txn {self.payment_transaction_id} [{self.status}]"


class CashCollectionRecord(models.Model):
    """Record of cash paid directly to the assigned cook for a visit."""

    STATUS_REPORTED = "reported"
    STATUS_CONFIRMED = "confirmed"
    STATUS_DISPUTED = "disputed"
    STATUS_RESOLVED = "resolved"

    STATUS_CHOICES = (
        (STATUS_REPORTED, "Reported by Cook"),
        (STATUS_CONFIRMED, "Confirmed by Household"),
        (STATUS_DISPUTED, "Disputed by Household"),
        (STATUS_RESOLVED, "Resolved by Admin"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(Booking, on_delete=models.PROTECT, related_name="cash_collection")
    cook = models.ForeignKey(CookProfile, on_delete=models.PROTECT, related_name="cash_collections")
    household = models.ForeignKey(Household, on_delete=models.PROTECT, related_name="cash_collections")
    reported_amount_minor_units = models.BigIntegerField()
    collected_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_REPORTED, db_index=True)
    cook_notes = models.TextField(blank=True, default="")
    household_dispute_reason = models.TextField(blank=True, default="")
    admin_resolution_notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "finance_cash_collection"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"CashCollection for Booking {self.booking_id} [{self.status}] ({self.reported_amount_minor_units})"


class CommissionLedger(models.Model):
    """Tracks platform commission liabilities and settlements for cooks."""

    TYPE_COMMISSION_ACCRUED = "commission_accrued"
    TYPE_COMMISSION_DEDUCTED = "commission_deducted"
    TYPE_COMMISSION_SETTLED = "commission_settled"

    TYPE_CHOICES = (
        (TYPE_COMMISSION_ACCRUED, "Commission Accrued (Cash Liability)"),
        (TYPE_COMMISSION_DEDUCTED, "Commission Deducted (Online Offset)"),
        (TYPE_COMMISSION_SETTLED, "Commission Settled"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cook = models.ForeignKey(CookProfile, on_delete=models.CASCADE, related_name="commission_ledger_entries")
    booking = models.ForeignKey(
        Booking,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="commission_ledger_entries",
    )
    entry_type = models.CharField(max_length=32, choices=TYPE_CHOICES, db_index=True)
    amount_minor_units = models.BigIntegerField(help_text="Commission amount in minor units.")
    running_balance_minor_units = models.BigIntegerField(
        default=0,
        help_text="Cumulative net commission owed by cook to the platform.",
    )
    description = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "finance_commission_ledger"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Ledger {self.cook.user.email} - {self.entry_type}: {self.amount_minor_units} (Bal: {self.running_balance_minor_units})"


class CookPayoutRecord(models.Model):
    """Record of net earnings disbursement to a cook after commission reconciliation."""

    STATUS_PENDING = "pending"
    STATUS_PROCESSED = "processed"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSED, "Processed"),
        (STATUS_FAILED, "Failed"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cook = models.ForeignKey(CookProfile, on_delete=models.PROTECT, related_name="payout_records")
    period_start = models.DateField()
    period_end = models.DateField()
    gross_online_earnings_minor_units = models.BigIntegerField(default=0)
    commission_deductions_minor_units = models.BigIntegerField(default=0)
    net_payout_amount_minor_units = models.BigIntegerField(default=0)
    currency = models.CharField(max_length=3, default="INR")
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    reference_id = models.CharField(max_length=128, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "finance_cook_payout_record"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return (
            f"Payout {self.cook.user.email} [{self.status}]: Net {self.net_payout_amount_minor_units} {self.currency} "
            f"({self.period_start} to {self.period_end})"
        )
