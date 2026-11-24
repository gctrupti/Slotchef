"""Scheduling orchestration service: builds snapshots, executes CP-SAT, and transactionally commits proposals."""

from __future__ import annotations

import datetime
import uuid
from typing import Any

from django.db import IntegrityError, models, transaction

from apps.audit.models import AuditLog
from apps.bookings.models import Booking
from apps.communities.models import Society
from apps.cooks.models import CookAvailability, CookBreak, CookLeave, CookProfile
from apps.operations.models import OutboxEvent
from apps.scheduling.models import (
    CookAssignment,
    SchedulePlan,
    SchedulingConflict,
    SchedulingRun,
    TravelEstimate,
)
from slotchef_optimizer.models.domain import (
    BookingInput,
    BreakInterval,
    CookInput,
    LeavePeriod,
    SchedulingSnapshot,
    TimeWindow,
)
from slotchef_optimizer.solver.engine import SlotChefScheduler
from slotchef_optimizer.utils.time_utils import minutes_to_datetime


class ScheduleStaleConflictError(Exception):
    """Raised when a proposed assignment conflicts with a concurrent committed assignment."""


class SchedulingOrchestrator:
    """Coordinates snapshot extraction, CP-SAT solve, revalidation, and atomic database commit."""

    def __init__(self, solver_time_limit_seconds: float = 5.0, max_retries: int = 3) -> None:
        self.scheduler = SlotChefScheduler(time_limit_seconds=solver_time_limit_seconds)
        self.max_retries = max_retries

    def build_snapshot(
        self,
        society: Society,
        service_date: datetime.date,
        include_pending_bookings: bool = True,
    ) -> SchedulingSnapshot:
        """Extract database state into an immutable SchedulingSnapshot."""
        weekday = service_date.weekday()

        # 1. Eligible cooks for this society
        cook_qs = CookProfile.objects.filter(
            active_status=True,
            verification_status=CookProfile.VERIFICATION_VERIFIED,
        ).filter(
            models.Q(societies=society) | models.Q(societies__isnull=True)
        ).distinct()

        cook_inputs: list[CookInput] = []
        for cp in cook_qs:
            # Working windows: check specific_date overrides first, otherwise weekday
            windows: list[TimeWindow] = []
            avail_overrides = CookAvailability.objects.filter(cook=cp, specific_date=service_date)
            if avail_overrides.exists():
                for av in avail_overrides:
                    windows.append(TimeWindow(av.start_minute, av.end_minute))
            else:
                for av in CookAvailability.objects.filter(cook=cp, weekday=weekday):
                    windows.append(TimeWindow(av.start_minute, av.end_minute))

            # Breaks
            breaks: list[BreakInterval] = []
            break_overrides = CookBreak.objects.filter(cook=cp, specific_date=service_date)
            if break_overrides.exists():
                for brk in break_overrides:
                    breaks.append(BreakInterval(brk.start_minute, brk.end_minute, brk.reason))
            else:
                for brk in CookBreak.objects.filter(cook=cp, recurring_weekday=weekday):
                    breaks.append(BreakInterval(brk.start_minute, brk.end_minute, brk.reason))

            # Leaves
            leaves = [
                LeavePeriod(lv.start_date, lv.end_date, lv.status)
                for lv in CookLeave.objects.filter(
                    cook=cp,
                    status=CookLeave.STATUS_APPROVED,
                    start_date__lte=service_date,
                    end_date__gte=service_date,
                )
            ]

            # Skills
            skills = {cs.skill.code for cs in cp.skills.all()}

            # Work policy
            work_policy = getattr(cp, "work_policy", None)
            max_daily_mins = (
                work_policy.max_daily_minutes
                if work_policy and work_policy.max_daily_minutes < cp.max_daily_minutes
                else cp.max_daily_minutes
            )
            buffer_mins = work_policy.buffer_between_visits_minutes if work_policy else 5

            cook_inputs.append(
                CookInput(
                    id=str(cp.id),
                    name=cp.user.email,
                    is_active=cp.active_status,
                    is_verified=(cp.verification_status == CookProfile.VERIFICATION_VERIFIED),
                    authorized_societies={str(s.id) for s in cp.societies.all()},
                    skills=skills,
                    working_windows=windows,
                    breaks=breaks,
                    leaves=leaves,
                    max_daily_minutes=max_daily_mins,
                    max_daily_visits=cp.max_daily_visits,
                    default_buffer_minutes=buffer_mins,
                )
            )

        # 2. Bookings to schedule
        booking_status_filter = [Booking.STATUS_CONFIRMED]
        if include_pending_bookings:
            booking_status_filter.extend([Booking.STATUS_PENDING, Booking.STATUS_NEEDS_REVIEW])

        booking_qs = Booking.objects.filter(
            household__society=society,
            service_date=service_date,
            status__in=booking_status_filter,
        ).prefetch_related("requirements__skill")

        booking_inputs: list[BookingInput] = []
        for b in booking_qs:
            required_skills = {req.skill.code for req in b.requirements.all()}
            booking_inputs.append(
                BookingInput(
                    id=str(b.id),
                    household_id=str(b.household_id),
                    society_id=str(society.id),
                    earliest_start_minute=b.earliest_start_minute,
                    latest_finish_minute=b.latest_finish_minute,
                    duration_minutes=b.duration_minutes,
                    service_date=b.service_date,
                    required_skills=required_skills,
                    priority=b.priority,
                    preferred_cook_id=str(b.preferred_cook_id) if b.preferred_cook_id else None,
                    location_id=str(b.household.building_id),
                )
            )

        # 3. Travel estimates
        travel_matrix: dict[tuple[str, str], int] = {}
        for te in TravelEstimate.objects.all():
            travel_matrix[(te.from_location_id, te.to_location_id)] = te.estimated_minutes

        version_id = f"snap-{society.id}-{service_date}-{uuid.uuid4().hex[:8]}"
        return SchedulingSnapshot(
            snapshot_version=version_id,
            society_id=str(society.id),
            service_date=service_date,
            bookings=booking_inputs,
            cooks=cook_inputs,
            travel_matrix=travel_matrix,
            default_transition_minutes=5,
        )

    def run_and_commit(
        self,
        society: Society,
        service_date: datetime.date,
        actor: Any = None,
        correlation_id: str | None = None,
    ) -> tuple[SchedulePlan, SchedulingRun]:
        """Run optimization and atomically commit the proposed SchedulePlan and CookAssignments.

        Applies optimistic concurrency control, revalidating against concurrent commitments
        and retrying up to max_retries before falling back safely.
        """
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                with transaction.atomic():
                    snapshot = self.build_snapshot(society, service_date, include_pending_bookings=True)
                    solver_result = self.scheduler.solve(snapshot)

                    # Determine next version number for this society and date
                    latest_plan = (
                        SchedulePlan.objects.filter(society=society, service_date=service_date)
                        .order_by("-version")
                        .first()
                    )
                    next_version = (latest_plan.version + 1) if latest_plan else 1

                    # Supersede previous active plan and mark its assignments REPLACED
                    prev_plans = SchedulePlan.objects.filter(
                        society=society,
                        service_date=service_date,
                        status=SchedulePlan.STATUS_PUBLISHED,
                    )
                    for prev_plan in prev_plans:
                        CookAssignment.objects.filter(
                            schedule_plan=prev_plan,
                            status=CookAssignment.STATUS_CONFIRMED,
                        ).update(
                            status=CookAssignment.STATUS_REPLACED,
                            replacement_reason=f"Superseded by plan v{next_version}",
                        )
                    prev_plans.update(status=SchedulePlan.STATUS_SUPERSEDED)

                    plan = SchedulePlan.objects.create(
                        society=society,
                        service_date=service_date,
                        version=next_version,
                        status=SchedulePlan.STATUS_PUBLISHED,
                        solver_status=solver_result.status.value,
                        objective_summary=solver_result.objective_components,
                    )

                    # Record SchedulingRun audit
                    run = SchedulingRun.objects.create(
                        society=society,
                        service_date=service_date,
                        input_snapshot_version=snapshot.snapshot_version,
                        solver_status=solver_result.status.value,
                        solve_duration_ms=solver_result.solve_duration_ms,
                        objective_components=solver_result.objective_components,
                        reason_summary=solver_result.reason_summary,
                    )

                    # Revalidation and mapping commitments
                    for prop in solver_result.assignments:
                        booking = Booking.objects.select_for_update().get(id=prop.booking_id)
                        cook = CookProfile.objects.get(id=prop.cook_id)

                        # Revalidate against concurrent commitments
                        overlap_exists = (
                            CookAssignment.objects.filter(
                                cook=cook,
                                schedule_plan__service_date=service_date,
                                status__in=[
                                    CookAssignment.STATUS_CONFIRMED,
                                    CookAssignment.STATUS_STARTED,
                                    CookAssignment.STATUS_COMPLETED,
                                ],
                            )
                            .exclude(booking=booking)
                            .filter(
                                start_minute__lt=prop.end_minute,
                                end_minute__gt=prop.start_minute,
                            )
                            .exists()
                        )
                        if overlap_exists:
                            raise ScheduleStaleConflictError(
                                f"Concurrent conflict detected for cook {cook.id} at minutes {prop.start_minute}-{prop.end_minute}"
                            )

                        start_at = minutes_to_datetime(service_date, prop.start_minute, society.timezone)
                        end_at = minutes_to_datetime(service_date, prop.end_minute, society.timezone)

                        CookAssignment.objects.create(
                            booking=booking,
                            cook=cook,
                            schedule_plan=plan,
                            start_at=start_at,
                            end_at=end_at,
                            start_minute=prop.start_minute,
                            end_minute=prop.end_minute,
                            status=CookAssignment.STATUS_CONFIRMED,
                        )

                        # Confirm booking only when valid assignment is safely committed!
                        booking.status = Booking.STATUS_CONFIRMED
                        booking.save(update_fields=["status", "updated_at"])

                    # Map unassigned requests
                    for un in solver_result.unassigned:
                        booking = Booking.objects.select_for_update().get(id=un.booking_id)
                        booking.status = Booking.STATUS_UNFULFILLED
                        booking.save(update_fields=["status", "updated_at"])

                        SchedulingConflict.objects.create(
                            scheduling_run=run,
                            booking=booking,
                            primary_reason=un.primary_reason.value,
                            details={
                                "reason_details": un.reason_details,
                                "candidate_exclusions": {
                                    k: [c.value for c in v]
                                    for k, v in un.candidate_cook_exclusions.items()
                                },
                            },
                        )

                    # Audit log
                    AuditLog.objects.create(
                        actor=actor,
                        action="schedule.published",
                        entity_type="SchedulePlan",
                        entity_id=str(plan.id),
                        after_state={
                            "society_id": str(society.id),
                            "service_date": str(service_date),
                            "version": plan.version,
                            "assigned_count": len(solver_result.assignments),
                            "unassigned_count": len(solver_result.unassigned),
                            "solver_status": solver_result.status.value,
                        },
                        reason=f"Automated CP-SAT optimization {correlation_id or ''} (attempt {attempt})".strip(),
                    )

                    # Outbox event
                    OutboxEvent.objects.create(
                        event_type="schedule.published",
                        aggregate_type="SchedulePlan",
                        aggregate_id=str(plan.id),
                        payload={
                            "society_id": str(society.id),
                            "service_date": str(service_date),
                            "version": plan.version,
                            "assigned_bookings": [a.booking_id for a in solver_result.assignments],
                            "unassigned_bookings": [u.booking_id for u in solver_result.unassigned],
                        },
                    )

                    return plan, run

            except (ScheduleStaleConflictError, IntegrityError) as exc:
                last_error = exc
                continue

        # If retries exhausted, re-raise or handle
        if last_error:
            raise last_error
