from __future__ import annotations

import pytest
from rest_framework import exceptions

from config.exceptions import structured_exception_handler
from config.settings.base import build_postgres_config


def test_build_postgres_config_parses_supabase_direct_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DB_CONN_MAX_AGE", "120")
    monkeypatch.setenv("DB_SSLMODE", "require")
    monkeypatch.setenv("DB_DISABLE_SERVER_SIDE_CURSORS", "false")

    cfg = build_postgres_config(
        "postgresql://postgres:secret@db.example.supabase.co:5432/postgres"
    )

    assert cfg["ENGINE"] == "django.db.backends.postgresql"
    assert cfg["HOST"] == "db.example.supabase.co"
    assert cfg["PORT"] == 5432
    assert cfg["NAME"] == "postgres"
    assert cfg["USER"] == "postgres"
    assert cfg["CONN_MAX_AGE"] == 120
    assert cfg["CONN_HEALTH_CHECKS"] is True
    assert cfg["DISABLE_SERVER_SIDE_CURSORS"] is False
    assert cfg["OPTIONS"]["sslmode"] == "require"


def test_build_postgres_config_falls_back_to_discrete_env_vars(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("POSTGRES_HOST", "aws-0-ap-southeast-2.pooler.supabase.com")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.setenv("POSTGRES_DB", "postgres")
    monkeypatch.setenv("POSTGRES_USER", "postgres.projectref")
    monkeypatch.setenv("POSTGRES_PASSWORD", "secret")

    cfg = build_postgres_config("")

    assert cfg["ENGINE"] == "django.db.backends.postgresql"
    assert cfg["HOST"] == "aws-0-ap-southeast-2.pooler.supabase.com"
    assert cfg["USER"] == "postgres.projectref"
    assert cfg["OPTIONS"]["sslmode"] == "require"


def test_structured_exception_handler_formats_auth_error() -> None:
    exc = exceptions.NotAuthenticated()
    response = structured_exception_handler(exc, {"view": None, "request": None})

    assert response is not None
    assert response.status_code == 401
    assert response.data["error"]["code"] == "AUTHENTICATION_REQUIRED"

