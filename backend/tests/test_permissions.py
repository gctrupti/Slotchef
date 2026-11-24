"""Tests for role-based and object-level authorization."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from apps.communities.models import Building, Society
from apps.cooks.models import CookProfile
from apps.households.models import Household, HouseholdMember
from apps.households.permissions import IsHouseholdPrimaryResident, IsHouseholdResident
from apps.identity.models import Role, User, UserRole
from apps.identity.permissions import IsCook, IsHouseholdMember, IsPlatformAdmin, IsSocietyAdmin


@pytest.mark.django_db
def test_platform_and_society_admin_permissions() -> None:
    superuser = User.objects.create_superuser(email="root@example.com", password="RootPassword123!")
    regular_user = User.objects.create_user(email="user@example.com", password="UserPassword123!")

    admin_role = Role.objects.create(code=Role.PLATFORM_ADMIN, name="Platform Admin")
    platform_admin_user = User.objects.create_user(email="admin@example.com", password="AdminPassword123!")
    UserRole.objects.create(user=platform_admin_user, role=admin_role)

    soc_role = Role.objects.create(code=Role.SOCIETY_ADMIN, name="Society Admin")
    society_admin_user = User.objects.create_user(email="soc_admin@example.com", password="SocPassword123!")
    UserRole.objects.create(user=society_admin_user, role=soc_role)

    perm_platform = IsPlatformAdmin()
    perm_society = IsSocietyAdmin()

    req_super = Mock(user=superuser)
    req_platform = Mock(user=platform_admin_user)
    req_society = Mock(user=society_admin_user)
    req_regular = Mock(user=regular_user)
    req_anon = Mock(user=Mock(is_authenticated=False))

    # Platform admin checks
    assert perm_platform.has_permission(req_super, None) is True
    assert perm_platform.has_permission(req_platform, None) is True
    assert perm_platform.has_permission(req_society, None) is False
    assert perm_platform.has_permission(req_regular, None) is False
    assert perm_platform.has_permission(req_anon, None) is False

    # Society admin checks
    assert perm_society.has_permission(req_super, None) is True
    assert perm_society.has_permission(req_platform, None) is True
    assert perm_society.has_permission(req_society, None) is True
    assert perm_society.has_permission(req_regular, None) is False


@pytest.mark.django_db
def test_cook_permission() -> None:
    cook_user = User.objects.create_user(email="cook@example.com", password="CookPassword123!")
    CookProfile.objects.create(
        user=cook_user,
        verification_status=CookProfile.VERIFICATION_VERIFIED,
        active_status=True,
    )

    inactive_cook_user = User.objects.create_user(email="inactive_cook@example.com", password="PassWord123!")
    CookProfile.objects.create(
        user=inactive_cook_user,
        verification_status=CookProfile.VERIFICATION_VERIFIED,
        active_status=False,
    )

    regular_user = User.objects.create_user(email="other@example.com", password="PassWord123!")

    perm = IsCook()
    assert perm.has_permission(Mock(user=cook_user), None) is True
    assert perm.has_permission(Mock(user=inactive_cook_user), None) is False
    assert perm.has_permission(Mock(user=regular_user), None) is False


@pytest.mark.django_db
def test_household_object_level_isolation() -> None:
    society = Society.objects.create(name="Skyline Enclave", address="100 Skyline Rd")
    building = Building.objects.create(society=society, name="Block A")

    household_1 = Household.objects.create(society=society, building=building, apartment_label="101")
    household_2 = Household.objects.create(society=society, building=building, apartment_label="102")

    user_primary = User.objects.create_user(email="h1_primary@example.com", password="PassWord123!")
    user_member = User.objects.create_user(email="h1_member@example.com", password="PassWord123!")
    user_other = User.objects.create_user(email="h2_primary@example.com", password="PassWord123!")

    HouseholdMember.objects.create(household=household_1, user=user_primary, role="primary")
    HouseholdMember.objects.create(household=household_1, user=user_member, role="member")
    HouseholdMember.objects.create(household=household_2, user=user_other, role="primary")

    perm_member = IsHouseholdMember()
    perm_resident_obj = IsHouseholdResident()
    perm_primary_obj = IsHouseholdPrimaryResident()

    # Generic household member check
    assert perm_member.has_permission(Mock(user=user_primary), None) is True
    assert perm_member.has_permission(Mock(user=user_member), None) is True

    # Object-level isolation on household_1
    assert perm_resident_obj.has_object_permission(Mock(user=user_primary), None, household_1) is True
    assert perm_resident_obj.has_object_permission(Mock(user=user_member), None, household_1) is True
    # User from household_2 cannot access household_1
    assert perm_resident_obj.has_object_permission(Mock(user=user_other), None, household_1) is False

    # Primary resident checks
    assert perm_primary_obj.has_object_permission(Mock(user=user_primary), None, household_1) is True
    assert perm_primary_obj.has_object_permission(Mock(user=user_member), None, household_1) is False
    assert perm_primary_obj.has_object_permission(Mock(user=user_other), None, household_1) is False

