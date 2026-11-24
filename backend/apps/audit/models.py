"""Audit log domain model for recording sensitive state mutations."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """Immutable audit trail for scheduling, overrides, and sensitive mutations."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=128, db_index=True)
    entity_type = models.CharField(max_length=64, db_index=True)
    entity_id = models.CharField(max_length=128, db_index=True)
    before_state = models.JSONField(null=True, blank=True)
    after_state = models.JSONField(null=True, blank=True)
    reason = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "audit_log"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"[{self.created_at}] {self.action} on {self.entity_type} {self.entity_id}"
