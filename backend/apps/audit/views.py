"""Views for inspecting audit trails."""

from __future__ import annotations

from typing import Any

from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions
from rest_framework.request import Request
from rest_framework.response import Response

from apps.audit.models import AuditLog
from apps.audit.serializers import AuditLogSerializer
from apps.identity.models import Role


class AuditLogListView(generics.ListAPIView):
    """Retrieve immutable audit log records for administrative oversight."""

    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="List immutable system audit logs")
    def get_queryset(self) -> QuerySet[AuditLog]:
        user = self.request.user
        if not (user.is_superuser or user.has_role(Role.PLATFORM_ADMIN) or user.has_role(Role.SOCIETY_ADMIN)):
            return AuditLog.objects.none()

        qs = AuditLog.objects.select_related("actor").all()
        action = self.request.query_params.get("action")
        if action:
            qs = qs.filter(action=action)
        entity_type = self.request.query_params.get("entity_type")
        if entity_type:
            qs = qs.filter(entity_type=entity_type)

        limit_param = self.request.query_params.get("limit")
        if limit_param and limit_param.isdigit():
            return qs[: int(limit_param)]
        return qs

