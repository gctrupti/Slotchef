"""Views for Household domain."""

from __future__ import annotations

from typing import Any

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import AuditLog
from apps.households.models import Household, HouseholdVerificationProfile
from apps.households.permissions import IsHouseholdResident
from apps.households.serializers import (
    HouseholdSerializer,
    HouseholdVerificationProfileSerializer,
    HouseholdVerificationReviewSerializer,
)
from apps.identity.models import Role


class HouseholdListCreateView(generics.ListCreateAPIView):
    """List households the user has access to, or create a new household."""

    serializer_class = HouseholdSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[Household]:
        user = self.request.user
        if user.is_superuser or user.has_role(Role.PLATFORM_ADMIN):
            return Household.objects.select_related("society", "building").prefetch_related("members").all()
        # Non-admins only see households where they are registered members
        return (
            Household.objects.filter(members__user=user, members__is_active=True)
            .select_related("society", "building")
            .prefetch_related("members")
            .distinct()
        )

    def perform_create(self, serializer: HouseholdSerializer) -> None:
        serializer.save()


class HouseholdDetailView(generics.RetrieveAPIView):
    """Retrieve details of a specific household."""

    queryset = (
        Household.objects.select_related("society", "building")
        .prefetch_related("members")
        .all()
    )
    serializer_class = HouseholdSerializer
    permission_classes = [permissions.IsAuthenticated, IsHouseholdResident]


class HouseholdVerificationSelfView(APIView):
    """Retrieve or submit residency verification for a household."""

    permission_classes = [permissions.IsAuthenticated, IsHouseholdResident]

    @extend_schema(responses={200: HouseholdVerificationProfileSerializer}, summary="Get household residency verification")
    def get(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> Response:
        household = get_object_or_404(Household, pk=pk)
        self.check_object_permissions(request, household)

        profile, _ = HouseholdVerificationProfile.objects.get_or_create(household=household)
        return Response(HouseholdVerificationProfileSerializer(profile).data, status=status.HTTP_200_OK)

    @extend_schema(
        request=HouseholdVerificationProfileSerializer,
        responses={200: HouseholdVerificationProfileSerializer},
        summary="Submit household residency verification proof",
    )
    def post(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> Response:
        household = get_object_or_404(Household, pk=pk)
        self.check_object_permissions(request, household)

        profile, _ = HouseholdVerificationProfile.objects.get_or_create(household=household)
        serializer = HouseholdVerificationProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save(status=HouseholdVerificationProfile.STATUS_IN_REVIEW)
        return Response(HouseholdVerificationProfileSerializer(updated).data, status=status.HTTP_200_OK)


class AdminHouseholdVerificationDetailView(APIView):
    """Review and verify household residency status."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=HouseholdVerificationReviewSerializer,
        responses={200: HouseholdVerificationProfileSerializer},
        summary="Admin review household verification status",
    )
    def post(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> Response:
        if not (request.user.is_superuser or request.user.has_role(Role.PLATFORM_ADMIN) or request.user.has_role(Role.SOCIETY_ADMIN)):
            return Response({"detail": "Forbidden: Only administrators can verify households."}, status=status.HTTP_403_FORBIDDEN)

        verification = get_object_or_404(HouseholdVerificationProfile, household_id=pk)
        serializer = HouseholdVerificationReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data["status"]
        verification.status = new_status
        verification.admin_notes = serializer.validated_data.get("admin_notes", verification.admin_notes)
        if "society_noc_verified" in serializer.validated_data:
            verification.society_noc_verified = serializer.validated_data["society_noc_verified"]

        verification.reviewed_by = request.user
        verification.reviewed_at = timezone.now()
        verification.save()

        AuditLog.objects.create(
            actor=request.user,
            action="household.verification_reviewed",
            entity_type="HouseholdVerificationProfile",
            entity_id=str(verification.id),
            after_state={"status": new_status, "household_id": str(verification.household_id)},
        )

        return Response(HouseholdVerificationProfileSerializer(verification).data, status=status.HTTP_200_OK)

