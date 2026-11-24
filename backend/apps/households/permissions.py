"""Object-level permissions for household resources."""

from __future__ import annotations

from typing import Any

from rest_framework import permissions
from rest_framework.request import Request

from apps.identity.models import Role


class IsHouseholdResident(permissions.BasePermission):
    """Allows access only to users who are confirmed members of the target household."""

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or user.has_role(Role.PLATFORM_ADMIN):
            return True

        household = getattr(obj, "household", obj)
        return user.household_memberships.filter(household=household, is_active=True).exists()


class IsHouseholdPrimaryResident(permissions.BasePermission):
    """Allows modification only to the primary contact resident of the target household."""

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or user.has_role(Role.PLATFORM_ADMIN):
            return True

        household = getattr(obj, "household", obj)
        return user.household_memberships.filter(
            household=household,
            role="primary",
            is_active=True,
        ).exists()

