"""Role-based and object-level permissions for identity and general actors."""

from __future__ import annotations

from typing import Any

from rest_framework import permissions
from rest_framework.request import Request

from apps.identity.models import Role


class IsPlatformAdmin(permissions.BasePermission):
    """Allows access only to superusers or users assigned the platform_admin role."""

    def has_permission(self, request: Request, view: Any) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return bool(user.is_superuser or user.has_role(Role.PLATFORM_ADMIN))


class IsSocietyAdmin(permissions.BasePermission):
    """Allows access to society administrators or platform administrators."""

    def has_permission(self, request: Request, view: Any) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return bool(
            user.is_superuser
            or user.has_role(Role.PLATFORM_ADMIN)
            or user.has_role(Role.SOCIETY_ADMIN)
        )


class IsCook(permissions.BasePermission):
    """Allows access to verified active cook accounts."""

    def has_permission(self, request: Request, view: Any) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or user.has_role(Role.PLATFORM_ADMIN):
            return True
        return hasattr(user, "cook_profile") and user.cook_profile.active_status


class IsHouseholdMember(permissions.BasePermission):
    """Allows access to users who are active members of at least one household."""

    def has_permission(self, request: Request, view: Any) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or user.has_role(Role.PLATFORM_ADMIN):
            return True
        return user.household_memberships.filter(is_active=True).exists()

