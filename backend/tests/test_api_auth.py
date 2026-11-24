"""API integration tests for Identity domain (register, login, me)."""

from __future__ import annotations

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.identity.models import Role, User


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.mark.django_db
def test_user_registration_and_jwt_login(api_client: APIClient) -> None:
    # 1. Register a new resident user
    register_payload = {
        "email": "sarah.resident@example.com",
        "password": "StrongPassword123!",
        "phone": "+1234567890",
        "first_name": "Sarah",
        "last_name": "Resident",
        "role": Role.HOUSEHOLD_MEMBER,
    }
    reg_resp = api_client.post("/api/v1/auth/register", register_payload, format="json")
    assert reg_resp.status_code == status.HTTP_201_CREATED
    data = reg_resp.json()
    assert "access" in data
    assert "refresh" in data
    assert data["user"]["email"] == "sarah.resident@example.com"
    assert Role.HOUSEHOLD_MEMBER in data["user"]["roles"]

    # 2. Login with credentials
    login_resp = api_client.post(
        "/api/v1/auth/login",
        {"email": "sarah.resident@example.com", "password": "StrongPassword123!"},
        format="json",
    )
    assert login_resp.status_code == status.HTTP_200_OK
    token_data = login_resp.json()
    access_token = token_data["access"]
    assert access_token is not None

    # 3. Access /api/v1/me with JWT bearer token
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    me_resp = api_client.get("/api/v1/me")
    assert me_resp.status_code == status.HTTP_200_OK
    me_data = me_resp.json()
    assert me_data["email"] == "sarah.resident@example.com"
    assert me_data["first_name"] == "Sarah"


@pytest.mark.django_db
def test_registration_duplicate_email_rejected(api_client: APIClient) -> None:
    User.objects.create_user(email="duplicate@example.com", password="password123")

    resp = api_client.post(
        "/api/v1/auth/register",
        {
            "email": "duplicate@example.com",
            "password": "password123",
            "role": Role.HOUSEHOLD_MEMBER,
        },
        format="json",
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    err = resp.json()
    assert (
        "email" in err
        or "detail" in err
        or "email" in err.get("error", {}).get("details", {})
    )


@pytest.mark.django_db
def test_me_endpoint_requires_authentication(api_client: APIClient) -> None:
    resp = api_client.get("/api/v1/me")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
