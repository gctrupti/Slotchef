"""Views for Cook and Admin schedule inspection and controlled re-optimization."""

from __future__ import annotations

import datetime
from typing import Any

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.communities.models import Society
from apps.identity.permissions import IsSocietyAdmin
from apps.scheduling.models import CookAssignment, SchedulePlan, SchedulingConflict
from apps.scheduling.serializers import (
    CookAssignmentDetailSerializer,
    SchedulePlanDetailSerializer,
    SchedulingConflictSerializer,
)
from apps.scheduling.services.orchestrator import SchedulingOrchestrator
from config.exceptions import SlotChefAPIError


class CookScheduleMeView(APIView):
    """Retrieve schedule assignments for the currently authenticated cook."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: CookAssignmentDetailSerializer(many=True)}, summary="Current cook assigned schedule")
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = request.user
        if not hasattr(user, "cook_profile"):
            raise SlotChefAPIError(
                detail="User does not have an active cook profile.",
                code="FORBIDDEN",
                status_code=403,
            )

        cook = user.cook_profile
        target_date_str = request.query_params.get("date")

        qs = CookAssignment.objects.filter(
            cook=cook,
            status__in=[
                CookAssignment.STATUS_CONFIRMED,
                CookAssignment.STATUS_STARTED,
                CookAssignment.STATUS_COMPLETED,
            ],
        ).select_related("booking__household__building", "booking__household__society")

        if target_date_str:
            try:
                target_date = datetime.date.fromisoformat(target_date_str)
                qs = qs.filter(start_at__date=target_date)
            except ValueError:
                raise SlotChefAPIError(
                    detail="Invalid date format. Expected YYYY-MM-DD.",
                    code="VALIDATION_ERROR",
                    status_code=400,
                ) from None

        assignments = qs.order_by("start_at")
        return Response(
            {
                "cook_id": str(cook.id),
                "total_assignments": assignments.count(),
                "assignments": CookAssignmentDetailSerializer(assignments, many=True).data,
            },
            status=status.HTTP_200_OK,
        )


class AdminDailyScheduleView(APIView):
    """Inspect the active published schedule plan and unassigned conflicts for a target date."""

    permission_classes = [permissions.IsAuthenticated, IsSocietyAdmin]

    @extend_schema(responses={200: SchedulePlanDetailSerializer}, summary="Admin inspect published daily plan and conflicts")
    def get(self, request: Request, date: str, *args: Any, **kwargs: Any) -> Response:
        try:
            target_date = datetime.date.fromisoformat(date)
        except ValueError:
            raise SlotChefAPIError(
                detail="Invalid date format. Expected YYYY-MM-DD.",
                code="VALIDATION_ERROR",
                status_code=400,
            ) from None

        society_id = request.query_params.get("society_id")
        if society_id:
            society = get_object_or_404(Society, pk=society_id)
            plans = SchedulePlan.objects.filter(society=society, service_date=target_date)
        else:
            plans = SchedulePlan.objects.filter(service_date=target_date)

        published_plan = plans.filter(status=SchedulePlan.STATUS_PUBLISHED).first()
        if not published_plan:
            # Fall back to latest plan if none published
            published_plan = plans.order_by("-version").first()

        conflicts = SchedulingConflict.objects.filter(
            scheduling_run__service_date=target_date
        ).select_related("booking__household").order_by("-created_at")

        if society_id:
            conflicts = conflicts.filter(scheduling_run__society_id=society_id)

        return Response(
            {
                "service_date": str(target_date),
                "plan": SchedulePlanDetailSerializer(published_plan).data if published_plan else None,
                "unassigned_conflicts": SchedulingConflictSerializer(conflicts, many=True).data,
            },
            status=status.HTTP_200_OK,
        )


class AdminReoptimizeScheduleView(APIView):
    """Trigger controlled re-optimization of a daily schedule."""

    permission_classes = [permissions.IsAuthenticated, IsSocietyAdmin]

    @extend_schema(request=None, responses={200: SchedulePlanDetailSerializer}, summary="Admin trigger re-optimization for date")
    def post(self, request: Request, date: str, *args: Any, **kwargs: Any) -> Response:
        try:
            target_date = datetime.date.fromisoformat(date)
        except ValueError:
            raise SlotChefAPIError(
                detail="Invalid date format. Expected YYYY-MM-DD.",
                code="VALIDATION_ERROR",
                status_code=400,
            ) from None

        society_id = request.data.get("society_id") or request.query_params.get("society_id")
        if not society_id:
            society = Society.objects.first()
            if not society:
                raise SlotChefAPIError(
                    detail="No society found to reoptimize.",
                    code="VALIDATION_ERROR",
                    status_code=400,
                )
        else:
            society = get_object_or_404(Society, pk=society_id)

        orchestrator = SchedulingOrchestrator()
        plan, run = orchestrator.run_and_commit(
            society=society,
            service_date=target_date,
            actor=request.user,
            correlation_id="admin-reoptimize",
        )

        return Response(
            {
                "message": f"Successfully reoptimized schedule for {target_date}.",
                "plan": SchedulePlanDetailSerializer(plan).data,
                "solver_status": run.solver_status,
                "solve_duration_ms": run.solve_duration_ms,
            },
            status=status.HTTP_200_OK,
        )
