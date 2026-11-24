"""Serializers for Household domain."""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.households.models import (
    Household,
    HouseholdMember,
    HouseholdVerificationProfile,
)


class HouseholdMemberSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", read_only=True)
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = HouseholdMember
        fields = ["id", "user", "user_email", "user_name", "role", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]

    def get_user_name(self, obj: HouseholdMember) -> str:
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email


class HouseholdSerializer(serializers.ModelSerializer):
    members = HouseholdMemberSerializer(many=True, read_only=True)
    society_name = serializers.CharField(source="society.name", read_only=True)
    building_name = serializers.CharField(source="building.name", read_only=True)

    class Meta:
        model = Household
        fields = [
            "id",
            "society",
            "society_name",
            "building",
            "building_name",
            "apartment_label",
            "status",
            "notes",
            "members",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "members", "created_at", "updated_at"]

    def create(self, validated_data: dict[str, Any]) -> Household:
        user = self.context["request"].user
        household = Household.objects.create(**validated_data)
        # Automatically make creating user the primary resident
        HouseholdMember.objects.create(
            household=household,
            user=user,
            role=HouseholdMember.ROLE_PRIMARY,
            is_active=True,
        )
        return household


class HouseholdVerificationProfileSerializer(serializers.ModelSerializer):
    """Household residence and society proof verification record."""

    class Meta:
        model = HouseholdVerificationProfile
        fields = [
            "id",
            "household",
            "residency_type",
            "possession_proof_type",
            "possession_proof_reference",
            "society_noc_verified",
            "status",
            "admin_notes",
            "reviewed_by",
            "reviewed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "household",
            "society_noc_verified",
            "status",
            "admin_notes",
            "reviewed_by",
            "reviewed_at",
            "created_at",
            "updated_at",
        ]


class HouseholdVerificationReviewSerializer(serializers.Serializer):
    """Admin review of household residency proof."""

    status = serializers.ChoiceField(choices=HouseholdVerificationProfile.STATUS_CHOICES)
    society_noc_verified = serializers.BooleanField(required=False)
    admin_notes = serializers.CharField(required=False, allow_blank=True)


