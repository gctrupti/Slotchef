"""URL routing for Audit Log domain."""

from __future__ import annotations

from django.urls import path

from apps.audit.views import AuditLogListView

urlpatterns = [
    path("audit/logs", AuditLogListView.as_view(), name="audit-logs-list"),
]

