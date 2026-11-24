"""Operations models: Outbox events and API idempotency records."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class IdempotencyRecord(models.Model):
    """Stores client request hashes and serialized responses to prevent duplicates."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="idempotency_records",
    )
    endpoint = models.CharField(max_length=255, db_index=True)
    key = models.CharField(max_length=255, db_index=True)
    request_hash = models.CharField(max_length=128)
    response_status = models.PositiveIntegerField(default=200)
    response_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        db_table = "operation_idempotency"
        constraints = [
            models.UniqueConstraint(
                fields=["endpoint", "key"],
                name="unique_endpoint_idempotency_key",
            ),
        ]


class OutboxEvent(models.Model):
    """Reliable outbox event published transactionally alongside domain changes."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=128, db_index=True)
    aggregate_type = models.CharField(max_length=64, db_index=True)
    aggregate_id = models.CharField(max_length=128, db_index=True)
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True, db_index=True)
    attempt_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "operation_outbox_event"
        ordering = ["created_at"]
