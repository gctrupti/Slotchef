"""Custom authentication backend supporting login with email or phone number."""

from __future__ import annotations

from typing import Any

from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from rest_framework.request import Request

from apps.identity.models import User


class EmailOrPhoneBackend(ModelBackend):
    """Authenticate users using either their registered email address or mobile phone number."""

    def authenticate(
        self,
        request: Request | None = None,
        username: str | None = None,
        password: str | None = None,
        **kwargs: Any,
    ) -> User | None:
        identifier = username or kwargs.get("email") or kwargs.get("phone") or kwargs.get("identifier")
        if not identifier or not password:
            return None

        cleaned = str(identifier).strip()
        user = User.objects.filter(
            Q(email__iexact=cleaned) | Q(phone=cleaned)
        ).first()

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

