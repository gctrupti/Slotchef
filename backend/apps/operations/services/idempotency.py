"""Idempotency record management for mutating endpoints."""

from __future__ import annotations

import hashlib
import json
from datetime import timedelta
from typing import Any

from django.conf import settings
from django.utils import timezone

from apps.operations.models import IdempotencyRecord
from config.exceptions import SlotChefAPIError


def compute_request_hash(payload: Any) -> str:
    serialized = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def check_idempotency(
    actor: Any,
    endpoint: str,
    key: str,
    payload: Any,
) -> tuple[int, dict] | None:
    """Check if idempotency key was previously processed.

    Raises:
        SlotChefAPIError: if key was reused with a conflicting payload.
    """
    if not key:
        return None

    request_hash = compute_request_hash(payload)
    record = IdempotencyRecord.objects.filter(endpoint=endpoint, key=key).first()
    if not record:
        return None

    if record.request_hash != request_hash:
        raise SlotChefAPIError(
            detail="Idempotency key reused with different payload.",
            code="IDEMPOTENCY_KEY_REUSED_WITH_DIFFERENT_PAYLOAD",
            status_code=409,
        )

    return record.response_status, record.response_data


def record_idempotency(
    actor: Any,
    endpoint: str,
    key: str,
    payload: Any,
    status_code: int,
    response_data: dict,
) -> None:
    """Save an idempotent execution response."""
    if not key:
        return

    ttl_hours = getattr(settings, "IDEMPOTENCY_TTL_HOURS", 24)
    expires_at = timezone.now() + timedelta(hours=ttl_hours)
    request_hash = compute_request_hash(payload)

    sanitized_response = json.loads(json.dumps(response_data, default=str))

    IdempotencyRecord.objects.update_or_create(
        endpoint=endpoint,
        key=key,
        defaults={
            "actor": actor if getattr(actor, "is_authenticated", False) else None,
            "request_hash": request_hash,
            "response_status": status_code,
            "response_data": sanitized_response,
            "expires_at": expires_at,
        },
    )
