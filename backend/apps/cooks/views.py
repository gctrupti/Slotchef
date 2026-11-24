"""Views for Cook domain."""

from __future__ import annotations

from typing import Any

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import AuditLog
from apps.cooks.models import CookProfile, CookVerificationProfile
from apps.cooks.serializers import (
    CookAvailabilitySerializer,
    CookLeaveSerializer,
    CookProfileSerializer,
    CookVerificationProfileSerializer,
    CookVerificationReviewSerializer,
)


class CookListCreateView(generics.ListCreateAPIView):
    """List verified active cooks or onboard a cook profile."""

    serializer_class = CookProfileSerializer

    def get_permissions(self) -> list[permissions.BasePermission]:
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        user = self.request.user
        qs = (
            CookProfile.objects.select_related("user", "work_policy")
            .prefetch_related("skills__skill", "availabilities", "breaks", "leaves")
            .all()
        )
        if user.is_authenticated and (user.is_superuser or user.has_role("platform_admin") or user.has_role("society_admin")):
            return qs
        return qs.filter(active_status=True, verification_status=CookProfile.VERIFICATION_VERIFIED)


class CookDetailView(generics.RetrieveAPIView):
    """Retrieve details for a specific cook."""

    queryset = (
        CookProfile.objects.select_related("user", "work_policy")
        .prefetch_related("skills__skill", "availabilities", "breaks", "leaves")
        .all()
    )
    serializer_class = CookProfileSerializer
    permission_classes = [permissions.AllowAny]


class CookAvailabilityView(APIView):
    """Read or add/update availability working windows for a cook."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: CookAvailabilitySerializer(many=True)}, summary="Get cook working windows and breaks")
    def get(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> Response:
        cook = get_object_or_404(CookProfile, pk=pk)
        availabilities = cook.availabilities.all()
        breaks = cook.breaks.all()
        return Response(
            {
                "cook_id": str(cook.id),
                "availabilities": CookAvailabilitySerializer(availabilities, many=True).data,
                "breaks": [
                    {
                        "id": str(b.id),
                        "start_minute": b.start_minute,
                        "end_minute": b.end_minute,
                        "recurring_weekday": b.recurring_weekday,
                        "specific_date": str(b.specific_date) if b.specific_date else None,
                        "reason": b.reason,
                    }
                    for b in breaks
                ],
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(request=CookAvailabilitySerializer, responses={200: CookAvailabilitySerializer}, summary="Update cook availability window")
    def patch(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> Response:
        cook = get_object_or_404(CookProfile, pk=pk)
        # Check permission: user is the cook themselves or an admin
        if not (request.user.is_superuser or request.user == cook.user or request.user.has_role("platform_admin")):
            return Response(
                {"detail": "Forbidden: You cannot modify another cook's availability."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CookAvailabilitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        availability = serializer.save(cook=cook)
        return Response(CookAvailabilitySerializer(availability).data, status=status.HTTP_200_OK)


class CookLeaveCreateView(APIView):
    """Add scheduled leave for a cook."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=CookLeaveSerializer, responses={201: CookLeaveSerializer}, summary="Record scheduled leave for a cook")
    def post(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> Response:
        cook = get_object_or_404(CookProfile, pk=pk)
        if not (request.user.is_superuser or request.user == cook.user or request.user.has_role("platform_admin")):
            return Response(
                {"detail": "Forbidden: You cannot record leave for another cook."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CookLeaveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        leave = serializer.save(cook=cook)
        return Response(CookLeaveSerializer(leave).data, status=status.HTTP_201_CREATED)


class CookVerificationSelfView(APIView):
    """Retrieve or submit KYC and verification dossier for authenticated cook."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: CookVerificationProfileSerializer}, summary="Get authenticated cook verification profile")
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        if not hasattr(request.user, "cook_profile"):
            return Response({"detail": "User does not have an active cook profile."}, status=status.HTTP_404_NOT_FOUND)

        profile, _ = CookVerificationProfile.objects.get_or_create(cook=request.user.cook_profile)
        return Response(CookVerificationProfileSerializer(profile).data, status=status.HTTP_200_OK)

    @extend_schema(
        request=CookVerificationProfileSerializer,
        responses={200: CookVerificationProfileSerializer},
        summary="Submit or update cook verification dossier",
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        if not hasattr(request.user, "cook_profile"):
            return Response({"detail": "User does not have an active cook profile."}, status=status.HTTP_404_NOT_FOUND)

        profile, _ = CookVerificationProfile.objects.get_or_create(cook=request.user.cook_profile)
        serializer = CookVerificationProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save(status=CookVerificationProfile.STATUS_IN_REVIEW)

        from apps.identity.providers.kyc_provider import get_kyc_provider
        kyc = get_kyc_provider()
        bgv_res = kyc.run_background_check({"cook_id": str(profile.cook.id)})
        updated.background_verification_status = bgv_res.get("status", "pending")
        updated.background_verification_partner = bgv_res.get("partner", "")
        updated.background_verification_reference = bgv_res.get("reference", "")
        updated.save(update_fields=["background_verification_status", "background_verification_partner", "background_verification_reference"])

        return Response(CookVerificationProfileSerializer(updated).data, status=status.HTTP_200_OK)


class AdminCookVerificationDetailView(APIView):
    """Review and approve or reject cook verification dossier."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=CookVerificationReviewSerializer,
        responses={200: CookVerificationProfileSerializer},
        summary="Admin review cook verification dossier",
    )
    def post(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> Response:
        if not (request.user.is_superuser or request.user.has_role("platform_admin") or request.user.has_role("society_admin")):
            return Response({"detail": "Forbidden: Only administrators can review cook verifications."}, status=status.HTTP_403_FORBIDDEN)

        verification = get_object_or_404(CookVerificationProfile, cook_id=pk)
        serializer = CookVerificationReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data["status"]
        verification.status = new_status
        verification.admin_notes = serializer.validated_data.get("admin_notes", verification.admin_notes)
        if "reference_verified" in serializer.validated_data:
            verification.reference_verified = serializer.validated_data["reference_verified"]
        if "background_verification_status" in serializer.validated_data:
            verification.background_verification_status = serializer.validated_data["background_verification_status"]

        from django.utils import timezone
        verification.reviewed_by = request.user
        verification.reviewed_at = timezone.now()
        verification.save()

        # Synchronize cook profile verification status
        cook = verification.cook
        if new_status == CookVerificationProfile.STATUS_VERIFIED:
            cook.verification_status = CookProfile.VERIFICATION_VERIFIED
        elif new_status == CookVerificationProfile.STATUS_REJECTED:
            cook.verification_status = CookProfile.VERIFICATION_REJECTED
        cook.save(update_fields=["verification_status"])

        AuditLog.objects.create(
            actor=request.user,
            action="cook.verification_reviewed",
            entity_type="CookVerificationProfile",
            entity_id=str(verification.id),
            after_state={"status": new_status, "cook_id": str(cook.id)},
        )

        return Response(CookVerificationProfileSerializer(verification).data, status=status.HTTP_200_OK)

