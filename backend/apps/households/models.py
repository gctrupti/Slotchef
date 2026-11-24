"""Household and membership domain models."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.communities.models import Building, Society


class Household(models.Model):
    """Household unit requesting cooking services within a society."""

    STATUS_ACTIVE = "active"
    STATUS_INACTIVE = "inactive"
    STATUS_SUSPENDED = "suspended"

    STATUS_CHOICES = (
        (STATUS_ACTIVE, "Active"),
        (STATUS_INACTIVE, "Inactive"),
        (STATUS_SUSPENDED, "Suspended"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    society = models.ForeignKey(Society, on_delete=models.PROTECT, related_name="households")
    building = models.ForeignKey(Building, on_delete=models.PROTECT, related_name="households")
    apartment_label = models.CharField(max_length=64, help_text="Apartment number or door label")
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "household_household"
        ordering = ["society", "building", "apartment_label"]
        indexes = [
            models.Index(fields=["society", "status"], name="idx_household_soc_status"),
        ]

    def clean(self) -> None:
        super().clean()
        if (
            self.building_id
            and self.society_id
            and self.building.society_id != self.society_id
        ):
            raise ValidationError("Building does not belong to the selected society.")

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.society.name} - {self.building.name} - {self.apartment_label}"


class HouseholdMember(models.Model):
    """Authorized resident member linked to a household."""

    ROLE_PRIMARY = "primary"
    ROLE_MEMBER = "member"

    ROLE_CHOICES = (
        (ROLE_PRIMARY, "Primary Resident"),
        (ROLE_MEMBER, "Resident Member"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="household_memberships",
    )
    role = models.CharField(max_length=32, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "household_member"
        ordering = ["household", "-role", "created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["household", "user"],
                name="unique_household_user_membership",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user.email} in {self.household} ({self.role})"


class HouseholdVerificationProfile(models.Model):
    """Residency and society approval verification profile for a household."""

    RESIDENCY_OWNER = "owner"
    RESIDENCY_TENANT = "tenant"

    RESIDENCY_CHOICES = (
        (RESIDENCY_OWNER, "Owner"),
        (RESIDENCY_TENANT, "Tenant"),
    )

    PROOF_UTILITY_BILL = "utility_bill"
    PROOF_SALE_DEED = "sale_deed"
    PROOF_RENTAL_AGREEMENT = "rental_agreement"
    PROOF_MAINTENANCE_BILL = "society_maintenance_bill"

    PROOF_CHOICES = (
        (PROOF_UTILITY_BILL, "Electricity / Utility Bill"),
        (PROOF_SALE_DEED, "Property Sale Deed"),
        (PROOF_RENTAL_AGREEMENT, "Registered Rental Agreement"),
        (PROOF_MAINTENANCE_BILL, "Society Maintenance Receipt"),
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
    household = models.OneToOneField(
        Household,
        on_delete=models.CASCADE,
        related_name="verification_profile",
    )
    residency_type = models.CharField(max_length=32, choices=RESIDENCY_CHOICES, default=RESIDENCY_OWNER)
    possession_proof_type = models.CharField(max_length=64, choices=PROOF_CHOICES, default=PROOF_UTILITY_BILL)
    possession_proof_reference = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Secure reference to document proof",
    )
    society_noc_verified = models.BooleanField(
        default=False,
        help_text="Confirmed by society office or society admin",
    )
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )
    admin_notes = models.TextField(blank=True, default="")
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_household_verifications",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "household_verification_profile"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Verification for Household {self.household} [{self.status}]"

