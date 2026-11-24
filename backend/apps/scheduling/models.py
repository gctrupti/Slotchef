"""Scheduling plan, versioning, assignment, and conflict domain models."""

from __future__ import annotations

import uuid

from django.core.exceptions import ValidationError
from django.db import models

from apps.bookings.models import Booking
from apps.communities.models import Society
from apps.cooks.models import CookProfile


class SchedulePlan(models.Model):
    """Immutable versioned schedule plan for a society date horizon."""

    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_SUPERSEDED = "superseded"

    STATUS_CHOICES = (
        (STATUS_DRAFT, "Draft"),
        (STATUS_PUBLISHED, "Published"),
        (STATUS_SUPERSEDED, "Superseded"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    society = models.ForeignKey(Society, on_delete=models.PROTECT, related_name="schedule_plans")
    service_date = models.DateField(db_index=True)
    version = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_PUBLISHED)
    solver_status = models.CharField(max_length=32, default="OPTIMAL")
    objective_summary = models.JSONField(default=dict, blank=True)
    published_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "schedule_plan"
        ordering = ["society", "service_date", "-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["society", "service_date", "version"],
                name="unique_schedule_plan_version",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.society.name} Plan v{self.version} on {self.service_date} [{self.status}]"


class CookAssignment(models.Model):
    """Concrete commitment linking a booking to a cook at specific minutes."""

    STATUS_PROPOSED = "PROPOSED"
    STATUS_CONFIRMED = "CONFIRMED"
    STATUS_STARTED = "STARTED"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_REPLACED = "REPLACED"
    STATUS_MISSED = "MISSED"
    STATUS_DISPUTED = "DISPUTED"

    STATUS_CHOICES = (
        (STATUS_PROPOSED, "Proposed"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_STARTED, "Started"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_REPLACED, "Replaced"),
        (STATUS_MISSED, "Missed"),
        (STATUS_DISPUTED, "Disputed"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(Booking, on_delete=models.PROTECT, related_name="assignments")
    cook = models.ForeignKey(CookProfile, on_delete=models.PROTECT, related_name="assignments")
    schedule_plan = models.ForeignKey(SchedulePlan, on_delete=models.PROTECT, related_name="assignments")
    start_at = models.DateTimeField(db_index=True)
    end_at = models.DateTimeField(db_index=True)
    start_minute = models.PositiveIntegerField()
    end_minute = models.PositiveIntegerField()
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_CONFIRMED, db_index=True)
    replaced_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="replaces",
    )
    replacement_reason = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "schedule_cook_assignment"
        ordering = ["start_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_at__gt=models.F("start_at")),
                name="chk_assignment_end_after_start",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        if self.start_at and self.end_at and self.end_at <= self.start_at:
            raise ValidationError("Assignment end_at must be strictly after start_at.")

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Assignment {self.id}: Cook {self.cook.user.email} -> Booking {self.booking_id} [{self.status}]"


class SchedulingRun(models.Model):
    """Audit log of optimizer executions."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    society = models.ForeignKey(Society, on_delete=models.CASCADE, related_name="scheduling_runs")
    service_date = models.DateField(db_index=True)
    input_snapshot_version = models.CharField(max_length=64)
    solver_status = models.CharField(max_length=32)
    solve_duration_ms = models.PositiveIntegerField()
    objective_components = models.JSONField(default=dict, blank=True)
    reason_summary = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "schedule_run"
        ordering = ["-created_at"]


class SchedulingConflict(models.Model):
    """Detailed record of unassigned requests and cause."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scheduling_run = models.ForeignKey(SchedulingRun, on_delete=models.CASCADE, related_name="conflicts")
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="conflicts")
    primary_reason = models.CharField(max_length=64)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "schedule_conflict"


class TravelEstimate(models.Model):
    """Directional transition/travel minutes estimate between buildings or societies."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_location_id = models.CharField(max_length=128, db_index=True)
    to_location_id = models.CharField(max_length=128, db_index=True)
    estimated_minutes = models.PositiveIntegerField(default=5)
    source = models.CharField(max_length=64, default="static_society_default")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "schedule_travel_estimate"
        constraints = [
            models.UniqueConstraint(
                fields=["from_location_id", "to_location_id"],
                name="unique_travel_estimate_pair",
            ),
        ]
