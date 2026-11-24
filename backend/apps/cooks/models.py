"""Cook capacity, availability, leave, skills, and workload policy domain models."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.communities.models import Society


class CookProfile(models.Model):
    """Cook profile establishing identity, verification, and baseline capacity."""

    VERIFICATION_PENDING = "pending"
    VERIFICATION_VERIFIED = "verified"
    VERIFICATION_REJECTED = "rejected"
    VERIFICATION_SUSPENDED = "suspended"

    VERIFICATION_CHOICES = (
        (VERIFICATION_PENDING, "Pending"),
        (VERIFICATION_VERIFIED, "Verified"),
        (VERIFICATION_REJECTED, "Rejected"),
        (VERIFICATION_SUSPENDED, "Suspended"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cook_profile",
    )
    verification_status = models.CharField(
        max_length=32,
        choices=VERIFICATION_CHOICES,
        default=VERIFICATION_PENDING,
        db_index=True,
    )
    active_status = models.BooleanField(default=True, db_index=True)
    bio = models.TextField(blank=True, default="", help_text="Culinary background, philosophy, and specializations.")
    experience_years = models.PositiveIntegerField(default=3, help_text="Years of professional cooking experience.")
    max_daily_minutes = models.PositiveIntegerField(
        default=480,
        help_text="Maximum total cooking and transition minutes allowed per day.",
    )
    max_daily_visits = models.PositiveIntegerField(
        default=6,
        help_text="Maximum number of household cooking visits allowed per day.",
    )
    societies = models.ManyToManyField(
        Society,
        related_name="eligible_cooks",
        blank=True,
        help_text="Societies this cook is authorized to serve.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cook_profile"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Cook {self.user.email} [{self.verification_status}]"

    @property
    def is_eligible_to_work(self) -> bool:
        return self.active_status and self.verification_status == self.VERIFICATION_VERIFIED


class Skill(models.Model):
    """Recognized cooking capability or cuisine specialty."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cook_skill_catalog"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class CookSkill(models.Model):
    """Certified capability linking a cook to an approved skill."""

    LEVEL_BASIC = "basic"
    LEVEL_INTERMEDIATE = "intermediate"
    LEVEL_EXPERT = "expert"

    LEVEL_CHOICES = (
        (LEVEL_BASIC, "Basic"),
        (LEVEL_INTERMEDIATE, "Intermediate"),
        (LEVEL_EXPERT, "Expert"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cook = models.ForeignKey(CookProfile, on_delete=models.CASCADE, related_name="skills")
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name="cook_skills")
    proficiency_level = models.CharField(max_length=32, choices=LEVEL_CHOICES, default=LEVEL_INTERMEDIATE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cook_skill_assignment"
        ordering = ["cook", "skill"]
        constraints = [
            models.UniqueConstraint(fields=["cook", "skill"], name="unique_cook_skill"),
        ]

    def __str__(self) -> str:
        return f"{self.cook.user.email} - {self.skill.code} ({self.proficiency_level})"


class CookAvailability(models.Model):
    """Cook shift working windows (recurring weekday or specific date override)."""

    TYPE_REGULAR = "regular"
    TYPE_OVERRIDE = "override"

    TYPE_CHOICES = (
        (TYPE_REGULAR, "Regular"),
        (TYPE_OVERRIDE, "Override"),
    )

    WEEKDAY_CHOICES = (
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cook = models.ForeignKey(CookProfile, on_delete=models.CASCADE, related_name="availabilities")
    weekday = models.IntegerField(null=True, blank=True, choices=WEEKDAY_CHOICES)
    specific_date = models.DateField(null=True, blank=True)
    start_minute = models.PositiveIntegerField(help_text="Start minute from midnight (0-1440)")
    end_minute = models.PositiveIntegerField(help_text="End minute from midnight (0-1440)")
    availability_type = models.CharField(max_length=32, choices=TYPE_CHOICES, default=TYPE_REGULAR)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cook_availability"
        ordering = ["cook", "weekday", "specific_date", "start_minute"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(start_minute__lt=models.F("end_minute")) & models.Q(end_minute__lte=1440),
                name="chk_cook_avail_time_window",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        if self.weekday is None and self.specific_date is None:
            raise ValidationError("Either weekday or specific_date must be provided.")
        if self.start_minute >= self.end_minute:
            raise ValidationError("start_minute must be strictly less than end_minute.")
        if self.end_minute > 1440:
            raise ValidationError("end_minute cannot exceed 1440 (midnight).")

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        target = f"Weekday {self.weekday}" if self.weekday is not None else str(self.specific_date)
        return f"{self.cook.user.email} | {target}: {self.start_minute:02d}-{self.end_minute:02d}m"


class CookBreak(models.Model):
    """Protected rest/meal breaks that the scheduler cannot consume."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cook = models.ForeignKey(CookProfile, on_delete=models.CASCADE, related_name="breaks")
    specific_date = models.DateField(null=True, blank=True)
    recurring_weekday = models.IntegerField(null=True, blank=True, choices=CookAvailability.WEEKDAY_CHOICES)
    start_minute = models.PositiveIntegerField()
    end_minute = models.PositiveIntegerField()
    reason = models.CharField(max_length=128, blank=True, default="Rest break")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cook_break"
        ordering = ["cook", "start_minute"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(start_minute__lt=models.F("end_minute")) & models.Q(end_minute__lte=1440),
                name="chk_cook_break_time_window",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        if self.recurring_weekday is None and self.specific_date is None:
            raise ValidationError("Either recurring_weekday or specific_date must be specified.")
        if self.start_minute >= self.end_minute:
            raise ValidationError("start_minute must be strictly less than end_minute.")

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.cook.user.email} break {self.start_minute}-{self.end_minute}m"


class CookLeave(models.Model):
    """Cook scheduled leave/vacation period making the cook ineligible on target dates."""

    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"

    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cook = models.ForeignKey(CookProfile, on_delete=models.CASCADE, related_name="leaves")
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_APPROVED)
    reason = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cook_leave"
        ordering = ["-start_date"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(start_date__lte=models.F("end_date")),
                name="chk_cook_leave_dates_order",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError("start_date cannot be after end_date.")

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.cook.user.email} leave {self.start_date} to {self.end_date} [{self.status}]"


class CookWorkPolicy(models.Model):
    """Workload and welfare policy guarding consecutive visits and buffers."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cook = models.OneToOneField(CookProfile, on_delete=models.CASCADE, related_name="work_policy")
    max_consecutive_visits = models.PositiveIntegerField(
        default=4,
        help_text="Maximum consecutive cooking visits before a break is required.",
    )
    max_daily_minutes = models.PositiveIntegerField(
        default=480,
        help_text="Maximum total daily working minutes (overrides profile if more restrictive).",
    )
    buffer_between_visits_minutes = models.PositiveIntegerField(
        default=5,
        help_text="Default buffer/transition minutes required between home visits.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cook_work_policy"

    def __str__(self) -> str:
        return f"Policy for {self.cook.user.email}"


class CookVerificationProfile(models.Model):
    """Deep verification, background check, identity and skill audit for cooks."""

    DOC_AADHAAR = "aadhaar"
    DOC_PAN = "pan"
    DOC_DRIVING_LICENSE = "driving_license"
    DOC_VOTER_ID = "voter_id"
    DOC_PASSPORT = "passport"

    DOC_CHOICES = (
        (DOC_AADHAAR, "Aadhaar Card"),
        (DOC_PAN, "PAN Card"),
        (DOC_DRIVING_LICENSE, "Driving License"),
        (DOC_VOTER_ID, "Voter ID"),
        (DOC_PASSPORT, "Passport"),
    )

    BGV_PENDING = "pending"
    BGV_CLEAR = "clear"
    BGV_FLAGGED = "flagged"
    BGV_FAILED = "failed"

    BGV_CHOICES = (
        (BGV_PENDING, "Pending"),
        (BGV_CLEAR, "Clear"),
        (BGV_FLAGGED, "Flagged"),
        (BGV_FAILED, "Failed"),
    )

    STATUS_PENDING = "pending"
    STATUS_IN_REVIEW = "in_review"
    STATUS_VERIFIED = "verified"
    STATUS_REJECTED = "rejected"

    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending Review"),
        (STATUS_IN_REVIEW, "In Review"),
        (STATUS_VERIFIED, "Verified"),
        (STATUS_REJECTED, "Rejected"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cook = models.OneToOneField(
        CookProfile,
        on_delete=models.CASCADE,
        related_name="verification_profile",
    )
    document_type = models.CharField(max_length=32, choices=DOC_CHOICES, default=DOC_AADHAAR)
    masked_document_number = models.CharField(
        max_length=64,
        help_text="Masked identification number (e.g. XXXXXXXX1234) for privacy",
    )
    document_reference = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Encrypted or secure vault reference to original document",
    )
    address_proof_type = models.CharField(max_length=64, blank=True, default="utility_bill")
    address_proof_reference = models.CharField(max_length=255, blank=True, default="")
    years_of_experience = models.PositiveIntegerField(default=0)
    reference_contact_name = models.CharField(max_length=128, blank=True, default="")
    reference_contact_phone = models.CharField(max_length=32, blank=True, default="")
    reference_verified = models.BooleanField(default=False)
    background_verification_status = models.CharField(
        max_length=32,
        choices=BGV_CHOICES,
        default=BGV_PENDING,
    )
    background_verification_partner = models.CharField(max_length=64, blank=True, default="")
    background_verification_reference = models.CharField(max_length=128, blank=True, default="")
    skill_review_notes = models.TextField(blank=True, default="")
    admin_notes = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_cook_verifications",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cook_verification_profile"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Verification for Cook {self.cook.user.email} [{self.status}]"

