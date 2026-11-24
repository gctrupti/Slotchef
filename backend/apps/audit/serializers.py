"""Serializers for AuditLog model."""

from __future__ import annotations

from rest_framework import serializers

from apps.audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for immutable audit trail entries."""

    actor_email = serializers.EmailField(source="actor.email", read_only=True, default=None)
    actor_name = serializers.CharField(source="actor.get_full_name", read_only=True, default=None)

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "actor",
            "actor_email",
            "actor_name",
            "action",
            "entity_type",
            "entity_id",
            "before_state",
            "after_state",
            "reason",
            "created_at",
        ]
        read_only_fields = fields

