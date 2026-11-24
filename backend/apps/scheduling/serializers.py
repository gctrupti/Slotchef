"""Serializers for Scheduling domain."""

from __future__ import annotations

from rest_framework import serializers

from apps.scheduling.models import (
    CookAssignment,
    SchedulePlan,
    SchedulingConflict,
)


class CookAssignmentDetailSerializer(serializers.ModelSerializer):
    household_label = serializers.CharField(source="booking.household.apartment_label", read_only=True)
    building_name = serializers.CharField(source="booking.household.building.name", read_only=True)
    society_name = serializers.CharField(source="booking.household.society.name", read_only=True)
    meal_type = serializers.CharField(source="booking.meal_type", read_only=True)
    notes = serializers.CharField(source="booking.notes", read_only=True)

    class Meta:
        model = CookAssignment
        fields = [
            "id",
            "booking",
            "household_label",
            "building_name",
            "society_name",
            "meal_type",
            "start_minute",
            "end_minute",
            "start_at",
            "end_at",
            "status",
            "notes",
        ]


class SchedulingConflictSerializer(serializers.ModelSerializer):
    household_label = serializers.CharField(source="booking.household.apartment_label", read_only=True)

    class Meta:
        model = SchedulingConflict
        fields = [
            "id",
            "booking",
            "household_label",
            "primary_reason",
            "details",
            "created_at",
        ]


class SchedulePlanDetailSerializer(serializers.ModelSerializer):
    assignments = CookAssignmentDetailSerializer(many=True, read_only=True)
    society_name = serializers.CharField(source="society.name", read_only=True)

    class Meta:
        model = SchedulePlan
        fields = [
            "id",
            "society",
            "society_name",
            "service_date",
            "version",
            "status",
            "solver_status",
            "objective_summary",
            "assignments",
            "published_at",
            "created_at",
        ]
