"""Serializers for Cook domain."""

from __future__ import annotations

from rest_framework import serializers

from apps.cooks.models import (
    CookAvailability,
    CookBreak,
    CookLeave,
    CookProfile,
    CookSkill,
    CookVerificationProfile,
    CookWorkPolicy,
    Skill,
)


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ["id", "code", "name", "description"]


class CookSkillSerializer(serializers.ModelSerializer):
    skill_code = serializers.CharField(source="skill.code", read_only=True)
    skill_name = serializers.CharField(source="skill.name", read_only=True)

    class Meta:
        model = CookSkill
        fields = ["id", "skill", "skill_code", "skill_name", "proficiency_level"]


class CookAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = CookAvailability
        fields = [
            "id",
            "cook",
            "weekday",
            "specific_date",
            "start_minute",
            "end_minute",
            "availability_type",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class CookBreakSerializer(serializers.ModelSerializer):
    class Meta:
        model = CookBreak
        fields = [
            "id",
            "cook",
            "specific_date",
            "recurring_weekday",
            "start_minute",
            "end_minute",
            "reason",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class CookLeaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = CookLeave
        fields = [
            "id",
            "cook",
            "start_date",
            "end_date",
            "status",
            "reason",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class CookWorkPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = CookWorkPolicy
        fields = [
            "id",
            "max_consecutive_visits",
            "max_daily_minutes",
            "buffer_between_visits_minutes",
        ]
        read_only_fields = ["id"]


class CookProfileSerializer(serializers.ModelSerializer):
    skills = CookSkillSerializer(many=True, read_only=True)
    availabilities = CookAvailabilitySerializer(many=True, read_only=True)
    breaks = CookBreakSerializer(many=True, read_only=True)
    leaves = CookLeaveSerializer(many=True, read_only=True)
    work_policy = CookWorkPolicySerializer(read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = CookProfile
        fields = [
            "id",
            "user",
            "user_email",
            "user_name",
            "verification_status",
            "active_status",
            "max_daily_minutes",
            "max_daily_visits",
            "societies",
            "skills",
            "availabilities",
            "breaks",
            "leaves",
            "work_policy",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_user_name(self, obj: CookProfile) -> str:
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email


class CookVerificationProfileSerializer(serializers.ModelSerializer):
    """Detailed verification record for cooks."""

    class Meta:
        model = CookVerificationProfile
        fields = [
            "id",
            "cook",
            "document_type",
            "masked_document_number",
            "document_reference",
            "address_proof_type",
            "address_proof_reference",
            "years_of_experience",
            "reference_contact_name",
            "reference_contact_phone",
            "reference_verified",
            "background_verification_status",
            "background_verification_partner",
            "background_verification_reference",
            "skill_review_notes",
            "admin_notes",
            "status",
            "reviewed_by",
            "reviewed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "cook",
            "reference_verified",
            "background_verification_status",
            "background_verification_partner",
            "background_verification_reference",
            "admin_notes",
            "status",
            "reviewed_by",
            "reviewed_at",
            "created_at",
            "updated_at",
        ]


class CookVerificationReviewSerializer(serializers.Serializer):
    """Admin review of cook verification dossier."""

    status = serializers.ChoiceField(choices=CookVerificationProfile.STATUS_CHOICES)
    background_verification_status = serializers.ChoiceField(
        choices=CookVerificationProfile.BGV_CHOICES,
        required=False,
    )
    background_verification_partner = serializers.CharField(required=False, allow_blank=True)
    background_verification_reference = serializers.CharField(required=False, allow_blank=True)
    reference_verified = serializers.BooleanField(required=False)
    admin_notes = serializers.CharField(required=False, allow_blank=True)

