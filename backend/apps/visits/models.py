"""Visit execution events, safety checks, SOS emergency handling, incident reporting, and trust operations."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.cooks.models import CookProfile
from apps.scheduling.models import CookAssignment


class VisitEvent(models.Model):
    """Operational timestamped lifecycle event for an assigned visit."""

    TYPE_CHECK_IN = "check_in"
    TYPE_CHECK_OUT = "check_out"
    TYPE_STARTED = "started"
    TYPE_COMPLETED = "completed"
    TYPE_ARRIVAL_CONFIRMED = "arrival_confirmed"
    TYPE_INCIDENT = "incident_reported"
    TYPE_SOS = "sos_triggered"
    TYPE_LOCATION_PING = "location_ping"

    TYPE_CHOICES = (
        (TYPE_CHECK_IN, "Check In"),
        (TYPE_CHECK_OUT, "Check Out"),
        (TYPE_STARTED, "Started"),
        (TYPE_COMPLETED, "Completed"),
        (TYPE_ARRIVAL_CONFIRMED, "Household Arrival Confirmed"),
        (TYPE_INCIDENT, "Incident Reported"),
        (TYPE_SOS, "SOS Triggered"),
        (TYPE_LOCATION_PING, "Location Ping"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment = models.ForeignKey(CookAssignment, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=32, choices=TYPE_CHOICES)
    recorded_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "visit_event"
        ordering = ["recorded_at"]

    def __str__(self) -> str:
        return f"{self.assignment_id} - {self.event_type} at {self.recorded_at}"


class VisitSafetyCheck(models.Model):
    """Real-time monitoring, arrival verification, overdue tracking and consent location."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment = models.OneToOneField(
        CookAssignment,
        on_delete=models.CASCADE,
        related_name="safety_check",
    )
    check_in_at = models.DateTimeField(null=True, blank=True)
    check_out_at = models.DateTimeField(null=True, blank=True)
    arrival_confirmed_at = models.DateTimeField(null=True, blank=True)
    arrival_confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="confirmed_arrivals",
    )
    is_overdue = models.BooleanField(default=False, db_index=True)
    overdue_reason = models.CharField(max_length=128, blank=True, default="")
    location_sharing_consented = models.BooleanField(default=False)
    last_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    last_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    last_location_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "visit_safety_check"

    def __str__(self) -> str:
        return f"SafetyCheck assignment={self.assignment_id} [Overdue: {self.is_overdue}]"


class EmergencyContact(models.Model):
    """User-nominated trusted contacts notified during emergencies or SOS."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="emergency_contacts",
    )
    name = models.CharField(max_length=128)
    phone = models.CharField(max_length=32)
    relationship = models.CharField(max_length=64, blank=True, default="Family")
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "visit_emergency_contact"
        ordering = ["-is_primary", "-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.phone}) for {self.user.email}"


class SOSIncident(models.Model):
    """Urgent emergency or safety alarm requiring immediate intervention and India 112 escalation."""

    SRC_COOK = "cook"
    SRC_HOUSEHOLD = "household"
    SRC_AUTOMATED = "automated"
    SRC_ADMIN = "admin"

    SOURCE_CHOICES = (
        (SRC_COOK, "Cook"),
        (SRC_HOUSEHOLD, "Household"),
        (SRC_AUTOMATED, "Automated Overdue Detection"),
        (SRC_ADMIN, "Platform Administrator"),
    )

    STATUS_TRIGGERED = "triggered"
    STATUS_ACKNOWLEDGED = "acknowledged"
    STATUS_ESCALATED = "escalated"
    STATUS_RESOLVED = "resolved"
    STATUS_FALSE_ALARM = "false_alarm"

    STATUS_CHOICES = (
        (STATUS_TRIGGERED, "Triggered"),
        (STATUS_ACKNOWLEDGED, "Acknowledged"),
        (STATUS_ESCALATED, "Escalated"),
        (STATUS_RESOLVED, "Resolved"),
        (STATUS_FALSE_ALARM, "False Alarm"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment = models.ForeignKey(
        CookAssignment,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="sos_incidents",
    )
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="triggered_sos_incidents",
    )
    trigger_source = models.CharField(max_length=32, choices=SOURCE_CHOICES)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    notes = models.TextField(blank=True, default="")
    india_112_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Standardized National Emergency helpline 112 metadata payload",
    )
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default=STATUS_TRIGGERED,
        db_index=True,
    )
    external_dispatch_confirmed = models.BooleanField(
        default=False,
        help_text="Must never be true unless an actual 112/police dispatch service explicitly confirms",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="resolved_sos_incidents",
    )

    class Meta:
        db_table = "visit_sos_incident"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"SOS [{self.status}] triggered by {self.triggered_by.email}"


class SafetyNotificationLog(models.Model):
    """Audit log of emergency and safety notifications dispatched via SMS, email, or push."""

    CHANNEL_SMS = "sms"
    CHANNEL_EMAIL = "email"
    CHANNEL_PUSH = "push"

    CHANNEL_CHOICES = (
        (CHANNEL_SMS, "SMS"),
        (CHANNEL_EMAIL, "Email"),
        (CHANNEL_PUSH, "Push"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sos_incident = models.ForeignKey(
        SOSIncident,
        on_delete=models.CASCADE,
        related_name="notification_logs",
    )
    recipient_name = models.CharField(max_length=128, blank=True, default="")
    recipient_target = models.CharField(max_length=255)
    channel = models.CharField(max_length=16, choices=CHANNEL_CHOICES)
    status = models.CharField(
        max_length=32,
        choices=[("sent", "Sent"), ("delivered", "Delivered"), ("failed", "Failed")],
        default="sent",
    )
    payload = models.JSONField(default=dict, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "visit_safety_notification_log"
        ordering = ["-sent_at"]

    def __str__(self) -> str:
        return f"SafetyNotification to {self.recipient_target} [{self.status}]"


class IncidentReport(models.Model):
    """Two-sided incident report filed by households, cooks, or operations."""

    CAT_DELAY = "delay"
    CAT_ABSENCE = "absence"
    CAT_EQUIPMENT = "equipment"
    CAT_INGREDIENT = "ingredient"
    CAT_BEHAVIOR = "behavior"
    CAT_HYGIENE = "hygiene"
    CAT_PROPERTY_DAMAGE = "property_damage"
    CAT_SAFETY = "safety"
    CAT_PAYMENT_DISPUTE = "payment_dispute"
    CAT_HARASSMENT = "harassment"
    CAT_OTHER = "other"

    CAT_CHOICES = (
        (CAT_DELAY, "Delay"),
        (CAT_ABSENCE, "Absence / Unavailability"),
        (CAT_EQUIPMENT, "Equipment Issue"),
        (CAT_INGREDIENT, "Ingredient Issue"),
        (CAT_BEHAVIOR, "Behavior Issue"),
        (CAT_HYGIENE, "Hygiene / Food Quality"),
        (CAT_PROPERTY_DAMAGE, "Property Damage"),
        (CAT_SAFETY, "Safety Concern"),
        (CAT_PAYMENT_DISPUTE, "Payment Dispute"),
        (CAT_HARASSMENT, "Harassment"),
        (CAT_OTHER, "Other"),
    )

    SEV_LOW = "low"
    SEV_MEDIUM = "medium"
    SEV_HIGH = "high"
    SEV_CRITICAL = "critical"

    SEV_CHOICES = (
        (SEV_LOW, "Low"),
        (SEV_MEDIUM, "Medium"),
        (SEV_HIGH, "High"),
        (SEV_CRITICAL, "Critical"),
    )

    STATUS_REPORTED = "reported"
    STATUS_UNDER_INVESTIGATION = "under_investigation"
    STATUS_ACTION_REQUIRED = "action_required"
    STATUS_RESOLVED = "resolved"
    STATUS_DISMISSED = "dismissed"
    STATUS_APPEALED = "appealed"

    STATUS_CHOICES = (
        (STATUS_REPORTED, "Reported"),
        (STATUS_UNDER_INVESTIGATION, "Under Investigation"),
        (STATUS_ACTION_REQUIRED, "Action Required"),
        (STATUS_RESOLVED, "Resolved"),
        (STATUS_DISMISSED, "Dismissed"),
        (STATUS_APPEALED, "Appealed"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment = models.ForeignKey(
        CookAssignment,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="incident_reports",
    )
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="filed_incidents",
    )
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="complaints_received",
    )
    category = models.CharField(max_length=32, choices=CAT_CHOICES, default=CAT_OTHER)
    severity = models.CharField(max_length=32, choices=SEV_CHOICES, default=SEV_MEDIUM)
    description = models.TextField()
    evidence_urls = models.JSONField(
        default=list,
        blank=True,
        help_text="Secure links to photos, documents, or supporting evidence",
    )
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default=STATUS_REPORTED,
        db_index=True,
    )
    investigation_notes = models.TextField(
        blank=True,
        default="",
        help_text="Confidential administrative notes visible strictly to Trust & Safety team",
    )
    assigned_investigator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_incidents",
    )
    resolution_summary = models.TextField(blank=True, default="")
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "visit_incident_report"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Incident {self.category} [{self.severity}] status={self.status}"


class IncidentAppeal(models.Model):
    """Appeal submitted by a respondent party challenging an incident resolution."""

    STATUS_SUBMITTED = "submitted"
    STATUS_UNDER_REVIEW = "under_review"
    STATUS_UPHELD = "upheld"
    STATUS_OVERTURNED = "overturned"

    STATUS_CHOICES = (
        (STATUS_SUBMITTED, "Submitted"),
        (STATUS_UNDER_REVIEW, "Under Review"),
        (STATUS_UPHELD, "Upheld"),
        (STATUS_OVERTURNED, "Overturned"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    incident = models.ForeignKey(
        IncidentReport,
        on_delete=models.CASCADE,
        related_name="appeals",
    )
    appellant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="filed_appeals",
    )
    reason = models.TextField()
    additional_evidence = models.JSONField(default=list, blank=True)
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default=STATUS_SUBMITTED,
        db_index=True,
    )
    decision_notes = models.TextField(blank=True, default="")
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="decided_appeals",
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "visit_incident_appeal"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Appeal on incident {self.incident_id} [{self.status}]"


class AccountRestriction(models.Model):
    """Enforced restrictions, suspensions, and bookings/payout holds with full audit trail."""

    RESTRICTION_WARNING = "warning"
    RESTRICTION_BOOKING_BLOCKED = "booking_blocked"
    RESTRICTION_PAYOUT_FROZEN = "payout_frozen"
    RESTRICTION_TEMPORARY_SUSPENSION = "temporary_suspension"
    RESTRICTION_PERMANENT_BAN = "permanent_ban"

    RESTRICTION_CHOICES = (
        (RESTRICTION_WARNING, "Formal Warning"),
        (RESTRICTION_BOOKING_BLOCKED, "Booking Privileges Blocked"),
        (RESTRICTION_PAYOUT_FROZEN, "Cook Payout Frozen"),
        (RESTRICTION_TEMPORARY_SUSPENSION, "Temporary Suspension"),
        (RESTRICTION_PERMANENT_BAN, "Permanent Ban"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="restrictions",
    )
    incident = models.ForeignKey(
        IncidentReport,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="imposed_restrictions",
    )
    restriction_type = models.CharField(max_length=32, choices=RESTRICTION_CHOICES)
    reason = models.TextField()
    is_active = models.BooleanField(default=True, db_index=True)
    imposed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="imposed_restrictions",
    )
    lifted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="lifted_restrictions",
    )
    lift_reason = models.TextField(blank=True, default="")
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "visit_account_restriction"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Restriction {self.restriction_type} on {self.user.email} [Active: {self.is_active}]"


class TwoSidedReview(models.Model):
    """Reciprocal verified ratings and moderated reviews between Households and Cooks."""

    MOD_PUBLISHED = "published"
    MOD_FLAGGED = "flagged"
    MOD_HIDDEN = "hidden"

    MOD_CHOICES = (
        (MOD_PUBLISHED, "Published"),
        (MOD_FLAGGED, "Flagged for Moderation"),
        (MOD_HIDDEN, "Hidden"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment = models.ForeignKey(
        CookAssignment,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reviews_given",
    )
    reviewee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reviews_received",
    )
    rating = models.PositiveSmallIntegerField(
        help_text="Star rating from 1 to 5",
    )
    feedback_tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Structured tags e.g. punctual, delicious, clean, polite",
    )
    comment = models.TextField(blank=True, default="")
    moderation_status = models.CharField(
        max_length=32,
        choices=MOD_CHOICES,
        default=MOD_PUBLISHED,
        db_index=True,
    )
    moderation_notes = models.TextField(blank=True, default="")
    moderated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="moderated_reviews",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "visit_two_sided_review"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["assignment", "reviewer"],
                name="unique_review_per_assignment_reviewer",
            ),
            models.CheckConstraint(
                condition=models.Q(rating__gte=1) & models.Q(rating__lte=5),
                name="chk_review_rating_range",
            ),
        ]

    def __str__(self) -> str:
        return f"Review {self.rating}* by {self.reviewer.email} -> {self.reviewee.email}"


class BackupProposal(models.Model):
    """Proposal to substitute an assigned cook when an incident or absence occurs."""

    STATUS_PROPOSED = "proposed"
    STATUS_ACCEPTED = "accepted"
    STATUS_REJECTED = "rejected"
    STATUS_EXPIRED = "expired"

    STATUS_CHOICES = (
        (STATUS_PROPOSED, "Proposed"),
        (STATUS_ACCEPTED, "Accepted"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_EXPIRED, "Expired"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    original_assignment = models.ForeignKey(
        CookAssignment,
        on_delete=models.CASCADE,
        related_name="backup_proposals",
    )
    proposed_cook = models.ForeignKey(CookProfile, on_delete=models.PROTECT, related_name="backup_proposals")
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_PROPOSED)
    reason = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "visit_backup_proposal"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Backup {self.proposed_cook} for {self.original_assignment_id} [{self.status}]"
