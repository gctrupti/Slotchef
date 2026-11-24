"""Pure Python domain representations for scheduling input and output."""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Any

from slotchef_optimizer.explanations.reasons import ReasonCode, SolverStatus


@dataclass(frozen=True)
class TimeWindow:
    """Integer minute time window [start, end]."""

    start_minute: int
    end_minute: int

    def __post_init__(self) -> None:
        if self.start_minute < 0 or self.end_minute > 1440:
            raise ValueError(f"TimeWindow [{self.start_minute}, {self.end_minute}] out of bounds 0..1440")
        if self.start_minute >= self.end_minute:
            raise ValueError(f"start_minute {self.start_minute} must be strictly less than end_minute {self.end_minute}")

    @property
    def span_minutes(self) -> int:
        return self.end_minute - self.start_minute


@dataclass(frozen=True)
class BreakInterval:
    """Protected break window."""

    start_minute: int
    end_minute: int
    reason: str = "Break"


@dataclass(frozen=True)
class LeavePeriod:
    """Leave period covering a date range."""

    start_date: datetime.date
    end_date: datetime.date
    status: str = "approved"

    def covers(self, target_date: datetime.date) -> bool:
        return self.status == "approved" and self.start_date <= target_date <= self.end_date


@dataclass
class CookInput:
    """Cook profile and capacity snapshot for a single planning day."""

    id: str
    name: str = ""
    is_active: bool = True
    is_verified: bool = True
    authorized_societies: set[str] = field(default_factory=set)
    skills: set[str] = field(default_factory=set)
    working_windows: list[TimeWindow] = field(default_factory=list)
    breaks: list[BreakInterval] = field(default_factory=list)
    leaves: list[LeavePeriod] = field(default_factory=list)
    max_daily_minutes: int = 480
    max_daily_visits: int = 6
    max_consecutive_visits: int = 4
    default_buffer_minutes: int = 5
    # Existing committed assignments for incremental/re-planning stability
    existing_commitments: list[tuple[int, int]] = field(default_factory=list)


@dataclass
class BookingInput:
    """Household cooking booking request."""

    id: str
    household_id: str
    society_id: str
    earliest_start_minute: int
    latest_finish_minute: int
    duration_minutes: int
    service_date: datetime.date
    required_skills: set[str] = field(default_factory=set)
    preferred_start_minute: int | None = None
    preferred_cook_id: str | None = None
    priority: int = 1  # 1 = normal, 2 = high, 3 = critical
    location_id: str = ""  # building/location identifier for travel calculation

    def __post_init__(self) -> None:
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")
        if self.latest_finish_minute - self.earliest_start_minute < self.duration_minutes:
            raise ValueError(
                f"Booking {self.id} window [{self.earliest_start_minute}, {self.latest_finish_minute}] "
                f"insufficient for duration {self.duration_minutes}m."
            )
        if self.preferred_start_minute is None:
            self.preferred_start_minute = self.earliest_start_minute


@dataclass
class SchedulingSnapshot:
    """Consistent immutable snapshot for a society date horizon."""

    snapshot_version: str
    society_id: str
    service_date: datetime.date
    bookings: list[BookingInput] = field(default_factory=list)
    cooks: list[CookInput] = field(default_factory=list)
    # Directional travel matrix: (from_loc, to_loc) -> minutes
    travel_matrix: dict[tuple[str, str], int] = field(default_factory=dict)
    default_transition_minutes: int = 5

    def get_transition_minutes(self, loc_a: str, loc_b: str) -> int:
        if loc_a == loc_b and loc_a:
            return self.default_transition_minutes
        return self.travel_matrix.get((loc_a, loc_b), self.default_transition_minutes)


@dataclass
class AssignmentProposal:
    """Proposed assignment for a single booking."""

    booking_id: str
    cook_id: str
    start_minute: int
    end_minute: int
    duration_minutes: int
    transition_before_minutes: int = 0
    transition_after_minutes: int = 0


@dataclass
class UnassignedProposal:
    """Detailed record for a booking that could not be assigned."""

    booking_id: str
    primary_reason: ReasonCode
    reason_details: str
    candidate_cook_exclusions: dict[str, list[ReasonCode]] = field(default_factory=dict)


@dataclass
class ScheduleResult:
    """Complete output of the scheduling engine."""

    status: SolverStatus
    solve_duration_ms: int
    assignments: list[AssignmentProposal] = field(default_factory=list)
    unassigned: list[UnassignedProposal] = field(default_factory=list)
    candidate_cook_count: int = 0
    objective_value: float = 0.0
    objective_components: dict[str, float] = field(default_factory=dict)
    reason_summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

