"""Serializers for Booking domain."""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.bookings.models import (
    Booking,
    BookingRequirement,
    HouseholdPackageSubscription,
    PackagePlan,
)
from apps.scheduling.models import CookAssignment, SchedulingConflict
from slotchef_optimizer.utils.time_utils import parse_time_to_minutes


class BookingRequirementSerializer(serializers.ModelSerializer):
    skill_code = serializers.CharField(source="skill.code", read_only=True)
    skill_name = serializers.CharField(source="skill.name", read_only=True)

    class Meta:
        model = BookingRequirement
        fields = ["id", "skill", "skill_code", "skill_name", "created_at"]
        read_only_fields = ["id", "created_at"]


class CookAssignmentSummarySerializer(serializers.ModelSerializer):
    cook_id = serializers.UUIDField(source="cook.id", read_only=True)
    cook_name = serializers.SerializerMethodField()

    class Meta:
        model = CookAssignment
        fields = [
            "id",
            "cook_id",
            "cook_name",
            "start_at",
            "end_at",
            "start_minute",
            "end_minute",
            "status",
        ]

    def get_cook_name(self, obj: CookAssignment) -> str:
        u = obj.cook.user
        return f"{u.first_name} {u.last_name}".strip() or u.email


class BookingCreateSerializer(serializers.Serializer):
    """Input serializer for household booking requests."""

    service_date = serializers.DateField()
    meal_type = serializers.ChoiceField(choices=Booking.MEAL_CHOICES, default=Booking.MEAL_BREAKFAST)
    earliest_start = serializers.CharField(required=False, help_text="HH:MM format, e.g. '07:30'")
    latest_finish = serializers.CharField(required=False, help_text="HH:MM format, e.g. '08:45'")
    earliest_start_minute = serializers.IntegerField(required=False, min_value=0, max_value=1440)
    latest_finish_minute = serializers.IntegerField(required=False, min_value=0, max_value=1440)
    estimated_duration_minutes = serializers.IntegerField(default=45, min_value=15, max_value=240)
    required_skills = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
    )
    dietary_tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
    )
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    priority = serializers.IntegerField(default=1, min_value=1, max_value=3)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        # Handle time format conversion
        if "earliest_start" in attrs:
            attrs["earliest_start_minute"] = parse_time_to_minutes(attrs["earliest_start"])
        if "latest_finish" in attrs:
            attrs["latest_finish_minute"] = parse_time_to_minutes(attrs["latest_finish"])

        start_min = attrs.get("earliest_start_minute")
        finish_min = attrs.get("latest_finish_minute")
        duration = attrs.get("estimated_duration_minutes", 45)

        if start_min is None or finish_min is None:
            raise serializers.ValidationError(
                "Either (earliest_start, latest_finish) or (earliest_start_minute, latest_finish_minute) must be provided."
            )

        if finish_min - start_min < duration:
            raise serializers.ValidationError(
                f"Time window ({finish_min - start_min} mins) is too narrow for requested duration ({duration} mins)."
            )

        return attrs


class BookingDetailSerializer(serializers.ModelSerializer):
    """Detailed booking serializer with requirements, assignment, and conflicts."""

    requirements = BookingRequirementSerializer(many=True, read_only=True)
    assignment = serializers.SerializerMethodField()
    conflict_reasons = serializers.SerializerMethodField()
    price_breakdown = serializers.SerializerMethodField()
    household_label = serializers.CharField(source="household.apartment_label", read_only=True)
    society_id = serializers.UUIDField(source="household.society_id", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "household",
            "household_label",
            "society_id",
            "service_date",
            "earliest_start_minute",
            "latest_finish_minute",
            "duration_minutes",
            "meal_type",
            "priority",
            "status",
            "notes",
            "requirements",
            "assignment",
            "conflict_reasons",
            "price_breakdown",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at"]

    def get_price_breakdown(self, obj: Booking) -> dict[str, Any] | None:
        if hasattr(obj, "price_breakdown"):
            b = obj.price_breakdown
            return {
                "base_fee_minor_units": b.base_fee_minor_units,
                "duration_fee_minor_units": b.duration_fee_minor_units,
                "meal_multiplier": float(b.meal_multiplier),
                "subtotal_minor_units": b.subtotal_minor_units,
                "platform_commission_minor_units": b.platform_commission_minor_units,
                "cook_earnings_minor_units": b.cook_earnings_minor_units,
                "tax_minor_units": b.tax_minor_units,
                "discount_minor_units": b.discount_minor_units,
                "total_amount_minor_units": b.total_amount_minor_units,
                "currency": b.currency,
            }
        return None

    def get_assignment(self, obj: Booking) -> dict[str, Any] | None:
        active_assignment = obj.assignments.filter(
            status__in=[
                CookAssignment.STATUS_CONFIRMED,
                CookAssignment.STATUS_STARTED,
                CookAssignment.STATUS_COMPLETED,
            ]
        ).first()
        if not active_assignment:
            return None
        return CookAssignmentSummarySerializer(active_assignment).data

    def get_conflict_reasons(self, obj: Booking) -> list[dict[str, Any]]:
        conflicts = SchedulingConflict.objects.filter(booking=obj).order_by("-created_at")
        return [
            {
                "primary_reason": c.primary_reason,
                "details": c.details,
                "created_at": c.created_at.isoformat(),
            }
            for c in conflicts
        ]


class PackagePlanSerializer(serializers.ModelSerializer):
    """Serializer for package plans (weekly, monthly, custom)."""

    society_name = serializers.CharField(source="society.name", read_only=True)

    class Meta:
        model = PackagePlan
        fields = [
            "id",
            "society",
            "society_name",
            "name",
            "code",
            "plan_type",
            "visit_frequency_per_week",
            "total_visits",
            "validity_days",
            "price_minor_units",
            "currency",
            "meal_type",
            "default_duration_minutes",
            "max_pause_days",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class HouseholdPackageSubscriptionSerializer(serializers.ModelSerializer):
    """Detailed subscription serializer tracking entitled, used, and remaining visits."""

    plan_name = serializers.CharField(source="package_plan.name", read_only=True)
    plan_code = serializers.CharField(source="package_plan.code", read_only=True)
    remaining_visits = serializers.IntegerField(read_only=True)
    preferred_cook_name = serializers.CharField(source="preferred_cook.user.get_full_name", read_only=True)

    class Meta:
        model = HouseholdPackageSubscription
        fields = [
            "id",
            "household",
            "package_plan",
            "plan_name",
            "plan_code",
            "status",
            "total_entitled_visits",
            "used_visits",
            "missed_visits",
            "cancelled_visits",
            "remaining_visits",
            "preferred_weekdays",
            "preferred_start_minute",
            "preferred_end_minute",
            "preferred_cook",
            "preferred_cook_name",
            "start_date",
            "end_date",
            "paused_at",
            "pause_resumes_at",
            "auto_renew",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class PackageSubscribeRequestSerializer(serializers.Serializer):
    """Request payload to subscribe household to a package plan."""

    package_plan_id = serializers.UUIDField()
    start_date = serializers.DateField()
    preferred_weekdays = serializers.ListField(
        child=serializers.IntegerField(min_value=0, max_value=6),
        required=False,
        default=list,
    )
    preferred_start = serializers.CharField(required=False, default="07:30")
    preferred_end = serializers.CharField(required=False, default="09:00")
    preferred_cook_id = serializers.UUIDField(required=False, allow_null=True)
    auto_renew = serializers.BooleanField(default=False)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        start_min = parse_time_to_minutes(attrs.get("preferred_start", "07:30"))
        end_min = parse_time_to_minutes(attrs.get("preferred_end", "09:00"))
        if end_min <= start_min:
            raise serializers.ValidationError("Preferred end time must be strictly after preferred start time.")
        attrs["preferred_start_minute"] = start_min
        attrs["preferred_end_minute"] = end_min
        return attrs


class PackagePauseRequestSerializer(serializers.Serializer):
    """Request payload to pause subscription."""

    pause_days = serializers.IntegerField(min_value=1, max_value=30)


class PackageCancelRequestSerializer(serializers.Serializer):
    """Request payload to cancel subscription."""

    cancellation_reason = serializers.CharField(required=False, allow_blank=True, default="")


class PackageRescheduleVisitRequestSerializer(serializers.Serializer):
    """Request payload to reschedule an individual package visit."""

    new_service_date = serializers.DateField()
    earliest_start = serializers.CharField(required=False, default="07:30")
    latest_finish = serializers.CharField(required=False, default="09:00")

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        start_min = parse_time_to_minutes(attrs.get("earliest_start", "07:30"))
        end_min = parse_time_to_minutes(attrs.get("latest_finish", "09:00"))
        if end_min <= start_min:
            raise serializers.ValidationError("Latest finish must be strictly after earliest start.")
        attrs["earliest_start_minute"] = start_min
        attrs["latest_finish_minute"] = end_min
        return attrs

