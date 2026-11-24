from __future__ import annotations

from unittest.mock import patch

from django.db import DatabaseError
from django.urls import reverse
from rest_framework.test import APIClient


def test_health_endpoint_ok(db) -> None:
    client = APIClient()
    response = client.get(reverse("health-check"))

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "slotchef-backend",
        "database": "ok",
    }


def test_health_endpoint_returns_503_when_database_fails() -> None:
    client = APIClient()
    with patch("config.views.connection.cursor", side_effect=DatabaseError("db down")):
        response = client.get(reverse("health-check"))

    assert response.status_code == 503
    assert response.json() == {
        "status": "degraded",
        "service": "slotchef-backend",
        "database": "unavailable",
    }


def test_openapi_schema_endpoint_exposes_health() -> None:
    client = APIClient()
    response = client.get(reverse("openapi-schema"), HTTP_ACCEPT="application/json")

    assert response.status_code == 200
    payload = response.json()
    assert "/api/v1/health" in payload["paths"]

