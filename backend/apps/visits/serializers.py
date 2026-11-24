"""Serializers for Visit operations, safety checks, SOS emergency handling, incidents, appeals, and two-sided reviews."""

from __future__ import annotations

from rest_framework import serializers

from apps.visits.models import (
    AccountRestriction,
    BackupProposal,
    EmergencyContact,
    IncidentAppeal,
    IncidentReport,
    SafetyNotificationLog,
    SOSIncident,
    TwoSidedReview,
    VisitEvent,
    VisitSafetyCheck,
)


class VisitEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitEvent
        fields = [
            "id",
            "assignment",
            "event_type",
            "recorded_at",
            "notes",
            "metadata",
        ]
        read_only_fields = ["id", "recorded_at"]


class VisitSafetyCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitSafetyCheck
        fields = [
            "id",
            "assignment",
            "check_in_at",
            "check_out_at",
            "arrival_confirmed_at",
            "arrival_confirmed_by",
            "is_overdue",
            "overdue_reason",
            "location_sharing_consented",
            "last_latitude",
            "last_longitude",
            "last_location_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "assignment",
            "check_in_at",
            "check_out_at",
            "arrival_confirmed_at",
            "arrival_confirmed_by",
            "is_overdue",
            "overdue_reason",
            "last_location_at",
            "created_at",
            "updated_at",
        ]


class EmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyContact
        fields = ["id", "user", "name", "phone", "relationship", "is_primary", "created_at"]
        read_only_fields = ["id", "user", "created_at"]


class SafetyNotificationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SafetyNotificationLog
        fields = ["id", "sos_incident", "recipient_name", "recipient_target", "channel", "status", "payload", "sent_at"]
        read_only_fields = ["id", "sent_at"]


class SOSIncidentSerializer(serializers.ModelSerializer):
    triggered_by_email = serializers.CharField(source="triggered_by.email", read_only=True)
    notification_logs = SafetyNotificationLogSerializer(many=True, read_only=True)

    class Meta:
        model = SOSIncident
        fields = [
            "id",
            "assignment",
            "triggered_by",
            "triggered_by_email",
            "trigger_source",
            "latitude",
            "longitude",
            "notes",
            "india_112_metadata",
            "status",
            "external_dispatch_confirmed",
            "notification_logs",
            "created_at",
            "resolved_at",
            "resolved_by",
        ]
        read_only_fields = [
            "id",
            "triggered_by",
            "triggered_by_email",
            "india_112_metadata",
            "external_dispatch_confirmed",
            "notification_logs",
            "created_at",
            "resolved_at",
            "resolved_by",
        ]


class IncidentReportSerializer(serializers.ModelSerializer):
    reported_by_email = serializers.CharField(source="reported_by.email", read_only=True)
    target_user_email = serializers.CharField(source="target_user.email", read_only=True)

    class Meta:
        model = IncidentReport
        fields = [
            "id",
            "assignment",
            "reported_by",
            "reported_by_email",
            "target_user",
            "target_user_email",
            "category",
            "severity",
            "description",
            "evidence_urls",
            "status",
            "investigation_notes",
            "assigned_investigator",
            "resolution_summary",
            "resolved_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "reported_by",
            "reported_by_email",
            "target_user_email",
            "status",
            "investigation_notes",
            "assigned_investigator",
            "resolution_summary",
            "resolved_at",
            "created_at",
        ]


class IncidentAppealSerializer(serializers.ModelSerializer):
    appellant_email = serializers.CharField(source="appellant.email", read_only=True)

    class Meta:
        model = IncidentAppeal
        fields = [
            "id",
            "incident",
            "appellant",
            "appellant_email",
            "reason",
            "additional_evidence",
            "status",
            "decision_notes",
            "decided_by",
            "decided_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "appellant",
            "appellant_email",
            "status",
            "decision_notes",
            "decided_by",
            "decided_at",
            "created_at",
        ]


class AccountRestrictionSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", read_only=True)
    imposed_by_email = serializers.CharField(source="imposed_by.email", read_only=True)

    class Meta:
        model = AccountRestriction
        fields = [
            "id",
            "user",
            "user_email",
            "incident",
            "restriction_type",
            "reason",
            "is_active",
            "imposed_by",
            "imposed_by_email",
            "lifted_by",
            "lift_reason",
            "expires_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "user_email",
            "is_active",
            "imposed_by",
            "imposed_by_email",
            "lifted_by",
            "lift_reason",
            "created_at",
        ]


class TwoSidedReviewSerializer(serializers.ModelSerializer):
    reviewer_email = serializers.CharField(source="reviewer.email", read_only=True)
    reviewee_email = serializers.CharField(source="reviewee.email", read_only=True)

    class Meta:
        model = TwoSidedReview
        fields = [
            "id",
            "assignment",
            "reviewer",
            "reviewer_email",
            "reviewee",
            "reviewee_email",
            "rating",
            "feedback_tags",
            "comment",
            "moderation_status",
            "moderation_notes",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "reviewer",
            "reviewer_email",
            "reviewee",
            "reviewee_email",
            "moderation_status",
            "moderation_notes",
            "created_at",
        ]


class BackupProposalSerializer(serializers.ModelSerializer):
    proposed_cook_name = serializers.SerializerMethodField()

    class Meta:
        model = BackupProposal
        fields = [
            "id",
            "original_assignment",
            "proposed_cook",
            "proposed_cook_name",
            "status",
            "reason",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_proposed_cook_name(self, obj: BackupProposal) -> str:
        u = obj.proposed_cook.user
        return f"{u.first_name} {u.last_name}".strip() or u.email
