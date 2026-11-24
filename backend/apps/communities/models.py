"""Community domain models (Society, Building, Apartment)."""

from __future__ import annotations

import uuid

from django.db import models


class Society(models.Model):
    """Apartment community / gated residential society."""

    STATUS_ACTIVE = "active"
    STATUS_INACTIVE = "inactive"

    STATUS_CHOICES = (
        (STATUS_ACTIVE, "Active"),
        (STATUS_INACTIVE, "Inactive"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, db_index=True)
    address = models.TextField()
    timezone = models.CharField(max_length=64, default="UTC")
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "community_society"
        ordering = ["name"]
        verbose_name_plural = "societies"

    def __str__(self) -> str:
        return self.name


class Building(models.Model):
    """Specific tower/block within a society."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    society = models.ForeignKey(Society, on_delete=models.CASCADE, related_name="buildings")
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=32, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "community_building"
        ordering = ["society", "name"]
        constraints = [
            models.UniqueConstraint(fields=["society", "name"], name="unique_building_per_society"),
        ]

    def __str__(self) -> str:
        return f"{self.society.name} - {self.name}"


class Apartment(models.Model):
    """Individual residential flat/apartment unit."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name="apartments")
    number = models.CharField(max_length=32)
    floor = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "community_apartment"
        ordering = ["building", "number"]
        constraints = [
            models.UniqueConstraint(fields=["building", "number"], name="unique_apartment_per_building"),
        ]

    def __str__(self) -> str:
        return f"{self.building.name} - #{self.number}"
