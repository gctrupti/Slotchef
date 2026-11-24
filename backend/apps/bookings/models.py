"""Booking demand and requirement domain models."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.communities.models import Society
from apps.cooks.models import CookProfile, Skill
from apps.households.models import Household


class Booking(models.Model):
    """Household cooking request with service window and status lifecycle."""

    STATUS_DRAFT = "DRAFT"
    STATUS_PENDING = "PENDING"
    STATUS_CONFIRMED = "CONFIRMED"
    STATUS_IN_PROGRESS = "IN_PROGRESS"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_UNFULFILLED = "UNFULFILLED"
    STATUS_NEEDS_REVIEW = "NEEDS_REVIEW"
    STATUS_REJECTED = "REJECTED"

    STATUS_CHOICES = (
        (STATUS_DRAFT, "Draft"),
        (STATUS_PENDING, "Pending"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_UNFULFILLED, "Unfulfilled"),
        (STATUS_NEEDS_REVIEW, "Needs Review"),
        (STATUS_REJECTED, "Rejected"),
    )

    MEAL_BREAKFAST = "breakfast"
    MEAL_LUNCH = "lunch"
    MEAL_DINNER = "dinner"
    MEAL_SNACKS = "snacks"

    MEAL_CHOICES = (
        (MEAL_BREAKFAST, "Breakfast"),
        (MEAL_LUNCH, "Lunch"),
        (MEAL_DINNER, "Dinner"),
        (MEAL_SNACKS, "Snacks"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    household = models.ForeignKey(Household, on_delete=models.PROTECT, related_name="bookings")
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_bookings",
    )
    service_date = models.DateField(db_index=True)
    earliest_start_minute = models.PositiveIntegerField(help_text="Earliest allowed start minute (0..1440)")
    latest_finish_minute = models.PositiveIntegerField(help_text="Latest allowed finish minute (0..1440)")
    duration_minutes = models.PositiveIntegerField(default=45)
    meal_type = models.CharField(max_length=32, choices=MEAL_CHOICES, default=MEAL_BREAKFAST)
    priority = models.PositiveIntegerField(default=1, help_text="Priority level (1=normal, 2=high, 3=urgent)")
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    idempotency_reference = models.CharField(max_length=128, blank=True, db_index=True)
    preferred_cook_id = models.UUIDField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "booking_booking"
        ordering = ["service_date", "earliest_start_minute"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(duration_minutes__gt=0),
                name="chk_booking_positive_duration",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    latest_finish_minute__gte=models.F("earliest_start_minute") + models.F("duration_minutes")
                ),
                name="chk_booking_window_accommodates_duration",
            ),
        ]
        indexes = [
            models.Index(fields=["service_date", "status"], name="idx_booking_date_status"),
        ]

    def clean(self) -> None:
        super().clean()
        if self.duration_minutes <= 0:
            raise ValidationError("Duration must be strictly positive.")
        if self.latest_finish_minute - self.earliest_start_minute < self.duration_minutes:
            raise ValidationError("Time window cannot accommodate the requested duration.")

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Booking {self.id} for {self.household} on {self.service_date} [{self.status}]"


class BookingRequirement(models.Model):
    """Specific skill, dietary tag, or capability required for a booking."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="requirements")
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name="booking_requirements")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "booking_requirement"
        constraints = [
            models.UniqueConstraint(fields=["booking", "skill"], name="unique_booking_skill_requirement"),
        ]


class MealPreference(models.Model):
    """Household recurring cuisine and dietary preferences."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name="meal_preferences")
    preference_key = models.CharField(max_length=64)
    preference_value = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "booking_meal_preference"


class ServiceDurationRule(models.Model):
    """Default service durations per meal type and household size."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meal_type = models.CharField(max_length=32, choices=Booking.MEAL_CHOICES, unique=True)
    default_duration_minutes = models.PositiveIntegerField(default=45)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "booking_duration_rule"


class PackagePlan(models.Model):
    """Catalog of subscription packages (weekly, monthly, custom)."""

    PLAN_WEEKLY = "weekly"
    PLAN_MONTHLY = "monthly"
    PLAN_CUSTOM = "custom"

    PLAN_CHOICES = (
        (PLAN_WEEKLY, "Weekly Package"),
        (PLAN_MONTHLY, "Monthly Package"),
        (PLAN_CUSTOM, "Custom Frequency Package"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    society = models.ForeignKey(
        Society,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="package_plans",
        help_text="Society-specific package; null indicates global platform plan.",
    )
    name = models.CharField(max_length=128)
    code = models.CharField(max_length=64, unique=True, db_index=True)
    plan_type = models.CharField(max_length=32, choices=PLAN_CHOICES, default=PLAN_WEEKLY)
    visit_frequency_per_week = models.PositiveIntegerField(
        default=5,
        help_text="Nominal visits per week (e.g. 5 days / week).",
    )
    total_visits = models.PositiveIntegerField(
        default=5,
        help_text="Total number of visits entitled within this package cycle.",
    )
    validity_days = models.PositiveIntegerField(
        default=7,
        help_text="Validity duration in calendar days (e.g. 7 for weekly, 30 for monthly).",
    )
    price_minor_units = models.BigIntegerField(
        default=95000,
        help_text="Package price in minor currency units (e.g. 95000 paise = 950 INR).",
    )
    currency = models.CharField(max_length=3, default="INR")
    meal_type = models.CharField(max_length=32, choices=Booking.MEAL_CHOICES, default=Booking.MEAL_BREAKFAST)
    default_duration_minutes = models.PositiveIntegerField(default=45)
    max_pause_days = models.PositiveIntegerField(
        default=7,
        help_text="Maximum total days this package can be paused.",
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "booking_package_plan"
        ordering = ["-is_active", "plan_type", "price_minor_units"]

    def __str__(self) -> str:
        soc = self.society.name if self.society else "Global"
        return f"{self.name} [{soc}] ({self.total_visits} visits / {self.validity_days}d)"


class HouseholdPackageSubscription(models.Model):
    """Active or historical package subscription enrolled by a household."""

    STATUS_ACTIVE = "active"
    STATUS_PAUSED = "paused"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"
    STATUS_EXPIRED = "expired"

    STATUS_CHOICES = (
        (STATUS_ACTIVE, "Active"),
        (STATUS_PAUSED, "Paused"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_EXPIRED, "Expired"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    household = models.ForeignKey(
        Household,
        on_delete=models.PROTECT,
        related_name="package_subscriptions",
    )
    package_plan = models.ForeignKey(
        PackagePlan,
        on_delete=models.PROTECT,
        related_name="subscriptions",
    )
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_ACTIVE, db_index=True)
    total_entitled_visits = models.PositiveIntegerField()
    used_visits = models.PositiveIntegerField(default=0)
    missed_visits = models.PositiveIntegerField(default=0)
    cancelled_visits = models.PositiveIntegerField(default=0)
    preferred_weekdays = models.JSONField(
        default=list,
        help_text="List of weekday integers (0=Monday, 6=Sunday) for recurring visits.",
    )
    preferred_start_minute = models.PositiveIntegerField(default=450)  # 07:30
    preferred_end_minute = models.PositiveIntegerField(default=540)  # 09:00
    preferred_cook = models.ForeignKey(
        CookProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="preferred_subscriptions",
    )
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)
    paused_at = models.DateTimeField(null=True, blank=True)
    pause_resumes_at = models.DateField(null=True, blank=True)
    auto_renew = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "booking_household_package_subscription"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["household", "status"], name="idx_sub_hh_status"),
        ]

    def __str__(self) -> str:
        return (
            f"Subscription {self.id}: {self.package_plan.name} for {self.household} "
            f"[{self.status}] ({self.used_visits}/{self.total_entitled_visits} used)"
        )

    @property
    def remaining_visits(self) -> int:
        """Unused visits remaining in subscription."""
        return max(0, self.total_entitled_visits - self.used_visits)


class PackageBookingLink(models.Model):
    """Audit link associating a generated Booking with its originating Package Subscription."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(
        HouseholdPackageSubscription,
        on_delete=models.CASCADE,
        related_name="booking_links",
    )
    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name="package_link",
    )
    is_missed = models.BooleanField(default=False)
    is_rescheduled = models.BooleanField(default=False)
    original_service_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "booking_package_booking_link"
        ordering = ["booking__service_date"]

    def __str__(self) -> str:
        return f"Link: Booking {self.booking_id} -> Sub {self.subscription_id}"
