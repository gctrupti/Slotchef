"""Views for Booking creation, status inspection, cancellation, and rescheduling."""

from __future__ import annotations

from typing import Any

from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import AuditLog
from apps.bookings.models import (
    Booking,
    BookingRequirement,
    HouseholdPackageSubscription,
    PackageBookingLink,
    PackagePlan,
)
from apps.bookings.serializers import (
    BookingCreateSerializer,
    BookingDetailSerializer,
    HouseholdPackageSubscriptionSerializer,
    PackageCancelRequestSerializer,
    PackagePauseRequestSerializer,
    PackagePlanSerializer,
    PackageRescheduleVisitRequestSerializer,
    PackageSubscribeRequestSerializer,
)
from apps.bookings.services.package_service import PackageService
from apps.cooks.models import Skill
from apps.finance.services.pricing_calculator import PricingCalculatorService
from apps.households.models import Household
from apps.identity.permissions import IsPlatformAdmin, IsSocietyAdmin
from apps.operations.models import OutboxEvent
from apps.operations.services.idempotency import check_idempotency, record_idempotency
from apps.scheduling.models import CookAssignment
from apps.scheduling.services.orchestrator import SchedulingOrchestrator
from config.exceptions import SlotChefAPIError


class HouseholdBookingCreateView(APIView):
    """Create a new booking request for a household with idempotent CP-SAT scheduling."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=BookingCreateSerializer,
        responses={201: BookingDetailSerializer},
        summary="Create household booking and trigger CP-SAT scheduler",
    )
    def post(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> Response:
        household = get_object_or_404(Household, pk=pk)

        # 1. Authorization: user must belong to household or be admin
        is_member = household.members.filter(user=request.user, is_active=True).exists()
        if not (request.user.is_superuser or request.user.has_role("platform_admin") or is_member):
            raise SlotChefAPIError(
                detail="Forbidden: You are not authorized to create bookings for this household.",
                code="FORBIDDEN",
                status_code=403,
            )

        if household.status == Household.STATUS_SUSPENDED:
            raise SlotChefAPIError(
                detail="Forbidden: Household account is suspended.",
                code="FORBIDDEN",
                status_code=403,
            )
        if hasattr(household, "verification_profile") and household.verification_profile.status in ["rejected", "suspended"]:
            raise SlotChefAPIError(
                detail="Forbidden: Household residence verification is rejected or suspended.",
                code="FORBIDDEN",
                status_code=403,
            )

        # 2. Check Idempotency
        idempotency_key = request.headers.get("Idempotency-Key", "").strip()
        endpoint_name = f"POST /api/v1/households/{pk}/bookings"
        if idempotency_key:
            cached = check_idempotency(request.user, endpoint_name, idempotency_key, request.data)
            if cached:
                cached_status, cached_data = cached
                return Response(cached_data, status=cached_status)

        # 3. Validate input
        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        with transaction.atomic():
            # 4. Create Booking as PENDING
            booking = Booking.objects.create(
                household=household,
                requested_by=request.user,
                service_date=data["service_date"],
                earliest_start_minute=data["earliest_start_minute"],
                latest_finish_minute=data["latest_finish_minute"],
                duration_minutes=data["estimated_duration_minutes"],
                meal_type=data["meal_type"],
                priority=data["priority"],
                status=Booking.STATUS_PENDING,
                idempotency_reference=idempotency_key,
                notes=data.get("notes", ""),
            )

            # 5. Link required skills
            for code in data.get("required_skills", []):
                skill, _ = Skill.objects.get_or_create(code=code, defaults={"name": code.title()})
                BookingRequirement.objects.create(booking=booking, skill=skill)

            # 6. Snapshot pricing calculation and breakdown
            PricingCalculatorService.calculate_price_breakdown(booking=booking, persist=True)

        # 7. Execute scheduling optimization and atomic database commit
        orchestrator = SchedulingOrchestrator()
        orchestrator.run_and_commit(
            society=household.society,
            service_date=data["service_date"],
            actor=request.user,
            correlation_id=f"booking-{booking.id}",
        )

        # 7. Reload booking to get finalized status and assignment
        booking.refresh_from_db()
        response_data = BookingDetailSerializer(booking).data

        # 8. Store idempotency record
        if idempotency_key:
            record_idempotency(
                actor=request.user,
                endpoint=endpoint_name,
                key=idempotency_key,
                payload=request.data,
                status_code=status.HTTP_201_CREATED,
                response_data=response_data,
            )

        return Response(response_data, status=status.HTTP_201_CREATED)


class BookingDetailView(APIView):
    """Retrieve booking details, assigned cook, or conflict explanations."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: BookingDetailSerializer}, summary="Get booking details and allocation")
    def get(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> Response:
        booking = get_object_or_404(
            Booking.objects.select_related("household__society", "requested_by")
            .prefetch_related("requirements__skill", "assignments__cook__user"),
            pk=pk,
        )

        # Authorization: household member, assigned cook, or admin
        is_member = booking.household.members.filter(user=request.user, is_active=True).exists()
        is_assigned_cook = hasattr(request.user, "cook_profile") and booking.assignments.filter(
            cook=request.user.cook_profile
        ).exists()

        if not (request.user.is_superuser or request.user.has_role("platform_admin") or is_member or is_assigned_cook):
            raise SlotChefAPIError(
                detail="Forbidden: You cannot inspect this booking.",
                code="FORBIDDEN",
                status_code=403,
            )

        return Response(BookingDetailSerializer(booking).data, status=status.HTTP_200_OK)


class BookingCancelView(APIView):
    """Cancel a booking under operational cancellation policy."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=None, responses={200: BookingDetailSerializer}, summary="Cancel booking")
    def post(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> Response:
        booking = get_object_or_404(Booking, pk=pk)

        # Authorization
        is_member = booking.household.members.filter(user=request.user, is_active=True).exists()
        if not (request.user.is_superuser or request.user.has_role("platform_admin") or is_member):
            raise SlotChefAPIError(
                detail="Forbidden: You cannot cancel this booking.",
                code="FORBIDDEN",
                status_code=403,
            )

        if booking.status in [Booking.STATUS_COMPLETED, Booking.STATUS_CANCELLED]:
            raise SlotChefAPIError(
                detail=f"Cannot cancel booking with status '{booking.status}'.",
                code="VALIDATION_ERROR",
                status_code=400,
            )

        with transaction.atomic():
            old_status = booking.status
            booking.status = Booking.STATUS_CANCELLED
            booking.save(update_fields=["status", "updated_at"])

            # Cancel active assignments
            booking.assignments.filter(
                status__in=[CookAssignment.STATUS_CONFIRMED, CookAssignment.STATUS_PROPOSED]
            ).update(status=CookAssignment.STATUS_CANCELLED, replacement_reason="Booking cancelled by user")

            AuditLog.objects.create(
                actor=request.user,
                action="booking.cancelled",
                entity_type="Booking",
                entity_id=str(booking.id),
                before_state={"status": old_status},
                after_state={"status": booking.status},
                reason=request.data.get("reason", "User requested cancellation"),
            )

            OutboxEvent.objects.create(
                event_type="booking.cancelled",
                aggregate_type="Booking",
                aggregate_id=str(booking.id),
                payload={"booking_id": str(booking.id), "household_id": str(booking.household_id)},
            )

        return Response(BookingDetailSerializer(booking).data, status=status.HTTP_200_OK)


class BookingRescheduleView(APIView):
    """Request rescheduling to an alternative date or time window."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=BookingCreateSerializer, responses={200: BookingDetailSerializer}, summary="Reschedule booking")
    def post(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> Response:
        booking = get_object_or_404(Booking, pk=pk)

        is_member = booking.household.members.filter(user=request.user, is_active=True).exists()
        if not (request.user.is_superuser or request.user.has_role("platform_admin") or is_member):
            raise SlotChefAPIError(
                detail="Forbidden: You cannot reschedule this booking.",
                code="FORBIDDEN",
                status_code=403,
            )

        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        with transaction.atomic():
            booking.service_date = data["service_date"]
            booking.earliest_start_minute = data["earliest_start_minute"]
            booking.latest_finish_minute = data["latest_finish_minute"]
            booking.duration_minutes = data["estimated_duration_minutes"]
            booking.meal_type = data["meal_type"]
            booking.status = Booking.STATUS_PENDING
            booking.save()

            # Mark existing assignments replaced/cancelled
            booking.assignments.filter(
                status__in=[CookAssignment.STATUS_CONFIRMED, CookAssignment.STATUS_PROPOSED]
            ).update(status=CookAssignment.STATUS_REPLACED, replacement_reason="Rescheduled by user")

        # Re-run optimizer
        orchestrator = SchedulingOrchestrator()
        orchestrator.run_and_commit(
            society=booking.household.society,
            service_date=data["service_date"],
            actor=request.user,
            correlation_id=f"reschedule-{booking.id}",
        )

        booking.refresh_from_db()
        return Response(BookingDetailSerializer(booking).data, status=status.HTTP_200_OK)


class PackagePlanListCreateView(APIView):
    """List available package plans or configure a new package (Admin only for creation)."""

    def get_permissions(self) -> list[Any]:
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), (IsPlatformAdmin | IsSocietyAdmin)()]
        return [permissions.IsAuthenticated()]

    @extend_schema(
        responses={200: PackagePlanSerializer(many=True)},
        summary="List active weekly and monthly package plans",
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        qs = PackagePlan.objects.filter(is_active=True).select_related("society")
        society_id = request.query_params.get("society_id")
        if society_id:
            qs = qs.filter(society_id=society_id)
        plan_type = request.query_params.get("plan_type")
        if plan_type:
            qs = qs.filter(plan_type=plan_type)

        return Response(PackagePlanSerializer(qs, many=True).data, status=status.HTTP_200_OK)

    @extend_schema(
        request=PackagePlanSerializer,
        responses={201: PackagePlanSerializer},
        summary="Create a new package plan (Admin only)",
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = PackagePlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plan = serializer.save()
        return Response(PackagePlanSerializer(plan).data, status=status.HTTP_201_CREATED)


class HouseholdPackageSubscribeView(APIView):
    """Enroll a household in a weekly or monthly package, scheduling visits via CP-SAT optimizer."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=PackageSubscribeRequestSerializer,
        responses={201: HouseholdPackageSubscriptionSerializer},
        summary="Subscribe household to a cooking package",
    )
    def post(self, request: Request, household_id: str, *args: Any, **kwargs: Any) -> Response:
        household = get_object_or_404(Household, id=household_id)

        # Check authorization: Resident member of household or admin
        is_member = household.members.filter(user=request.user, is_active=True).exists()
        is_admin = request.user.is_superuser or request.user.has_role("platform_admin")
        if not (is_member or is_admin):
            raise SlotChefAPIError("Forbidden: Cannot subscribe for this household.", code="FORBIDDEN", status_code=403)

        if household.status == Household.STATUS_SUSPENDED or (hasattr(household, "verification_profile") and household.verification_profile.status in ["rejected", "suspended"]):
            raise SlotChefAPIError("Forbidden: Household residence verification is rejected or suspended.", code="FORBIDDEN", status_code=403)

        serializer = PackageSubscribeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        plan = get_object_or_404(PackagePlan, id=data["package_plan_id"])

        sub, bookings = PackageService.subscribe_household(
            household=household,
            package_plan=plan,
            start_date=data["start_date"],
            preferred_weekdays=data.get("preferred_weekdays"),
            preferred_start_minute=data.get("preferred_start_minute", 450),
            preferred_end_minute=data.get("preferred_end_minute", 540),
            preferred_cook_id=str(data["preferred_cook_id"]) if data.get("preferred_cook_id") else None,
            auto_renew=data.get("auto_renew", False),
            actor=request.user,
        )

        response_data = HouseholdPackageSubscriptionSerializer(sub).data
        response_data["generated_bookings"] = [
            {
                "id": str(b.id),
                "service_date": str(b.service_date),
                "status": b.status,
                "meal_type": b.meal_type,
            }
            for b in bookings
        ]
        return Response(response_data, status=status.HTTP_201_CREATED)


class HouseholdPackageSubscriptionListView(APIView):
    """List subscriptions for a household."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={200: HouseholdPackageSubscriptionSerializer(many=True)},
        summary="List subscriptions and remaining visits for a household",
    )
    def get(self, request: Request, household_id: str, *args: Any, **kwargs: Any) -> Response:
        household = get_object_or_404(Household, id=household_id)
        is_member = household.members.filter(user=request.user, is_active=True).exists()
        is_admin = request.user.is_superuser or request.user.has_role("platform_admin")
        if not (is_member or is_admin):
            raise SlotChefAPIError("Forbidden: Cannot view subscriptions for this household.", code="FORBIDDEN", status_code=403)

        subs = HouseholdPackageSubscription.objects.filter(household=household).select_related("package_plan", "preferred_cook__user")
        return Response(HouseholdPackageSubscriptionSerializer(subs, many=True).data, status=status.HTTP_200_OK)


class PackageSubscriptionDetailView(APIView):
    """Retrieve full detail of a package subscription, including linked visits."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={200: HouseholdPackageSubscriptionSerializer},
        summary="Get subscription details and visit entitlement status",
    )
    def get(self, request: Request, subscription_id: str, *args: Any, **kwargs: Any) -> Response:
        sub = get_object_or_404(
            HouseholdPackageSubscription.objects.select_related("package_plan", "household", "preferred_cook__user"),
            id=subscription_id,
        )
        is_member = sub.household.members.filter(user=request.user, is_active=True).exists()
        is_admin = request.user.is_superuser or request.user.has_role("platform_admin")
        if not (is_member or is_admin):
            raise SlotChefAPIError("Forbidden", code="FORBIDDEN", status_code=403)

        data = HouseholdPackageSubscriptionSerializer(sub).data
        links = PackageBookingLink.objects.filter(subscription=sub).select_related("booking")
        data["visits"] = [
            {
                "booking_id": str(link.booking.id),
                "service_date": str(link.booking.service_date),
                "status": link.booking.status,
                "is_missed": link.is_missed,
                "is_rescheduled": link.is_rescheduled,
            }
            for link in links
        ]
        return Response(data, status=status.HTTP_200_OK)


class PackageSubscriptionPauseView(APIView):
    """Pause an active package subscription."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=PackagePauseRequestSerializer,
        responses={200: HouseholdPackageSubscriptionSerializer},
        summary="Pause package subscription",
    )
    def post(self, request: Request, subscription_id: str, *args: Any, **kwargs: Any) -> Response:
        sub = get_object_or_404(HouseholdPackageSubscription, id=subscription_id)
        is_member = sub.household.members.filter(user=request.user, is_active=True).exists()
        is_admin = request.user.is_superuser or request.user.has_role("platform_admin")
        if not (is_member or is_admin):
            raise SlotChefAPIError("Forbidden", code="FORBIDDEN", status_code=403)

        serializer = PackagePauseRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated = PackageService.pause_subscription(
            subscription=sub,
            pause_days=serializer.validated_data["pause_days"],
            actor=request.user,
        )
        return Response(HouseholdPackageSubscriptionSerializer(updated).data, status=status.HTTP_200_OK)


class PackageSubscriptionResumeView(APIView):
    """Resume a paused package subscription."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=None,
        responses={200: HouseholdPackageSubscriptionSerializer},
        summary="Resume paused package subscription",
    )
    def post(self, request: Request, subscription_id: str, *args: Any, **kwargs: Any) -> Response:
        sub = get_object_or_404(HouseholdPackageSubscription, id=subscription_id)
        is_member = sub.household.members.filter(user=request.user, is_active=True).exists()
        is_admin = request.user.is_superuser or request.user.has_role("platform_admin")
        if not (is_member or is_admin):
            raise SlotChefAPIError("Forbidden", code="FORBIDDEN", status_code=403)

        updated = PackageService.resume_subscription(subscription=sub, actor=request.user)
        return Response(HouseholdPackageSubscriptionSerializer(updated).data, status=status.HTTP_200_OK)


class PackageSubscriptionCancelView(APIView):
    """Cancel a package subscription and remaining future visits."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=PackageCancelRequestSerializer,
        responses={200: HouseholdPackageSubscriptionSerializer},
        summary="Cancel package subscription",
    )
    def post(self, request: Request, subscription_id: str, *args: Any, **kwargs: Any) -> Response:
        sub = get_object_or_404(HouseholdPackageSubscription, id=subscription_id)
        is_member = sub.household.members.filter(user=request.user, is_active=True).exists()
        is_admin = request.user.is_superuser or request.user.has_role("platform_admin")
        if not (is_member or is_admin):
            raise SlotChefAPIError("Forbidden", code="FORBIDDEN", status_code=403)

        serializer = PackageCancelRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated = PackageService.cancel_subscription(
            subscription=sub,
            reason=serializer.validated_data.get("cancellation_reason", ""),
            actor=request.user,
        )
        return Response(HouseholdPackageSubscriptionSerializer(updated).data, status=status.HTTP_200_OK)


class PackageVisitRescheduleView(APIView):
    """Reschedule a specific package visit within the subscription validity window."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=PackageRescheduleVisitRequestSerializer,
        responses={200: BookingDetailSerializer},
        summary="Reschedule a package visit within validity window",
    )
    def post(self, request: Request, booking_id: str, *args: Any, **kwargs: Any) -> Response:
        booking = get_object_or_404(Booking.objects.select_related("household"), id=booking_id)
        is_member = booking.household.members.filter(user=request.user, is_active=True).exists()
        is_admin = request.user.is_superuser or request.user.has_role("platform_admin")
        if not (is_member or is_admin):
            raise SlotChefAPIError("Forbidden", code="FORBIDDEN", status_code=403)

        serializer = PackageRescheduleVisitRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        rescheduled = PackageService.reschedule_package_visit(
            booking=booking,
            new_date=data["new_service_date"],
            new_start_minute=data["earliest_start_minute"],
            new_finish_minute=data["latest_finish_minute"],
            actor=request.user,
        )
        return Response(BookingDetailSerializer(rescheduled).data, status=status.HTTP_200_OK)

