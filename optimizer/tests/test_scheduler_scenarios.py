"""Comprehensive deterministic tests covering Section 16 mandatory scheduler scenarios."""

from __future__ import annotations

import datetime

import pytest

from slotchef_optimizer.explanations.reasons import ReasonCode, SolverStatus
from slotchef_optimizer.models.domain import (
    BookingInput,
    BreakInterval,
    CookInput,
    LeavePeriod,
    SchedulingSnapshot,
    TimeWindow,
)
from slotchef_optimizer.scenarios.alexa_conflict import make_alexa_conflict_scenario
from slotchef_optimizer.solver.engine import SlotChefScheduler


@pytest.fixture
def scheduler() -> SlotChefScheduler:
    return SlotChefScheduler(time_limit_seconds=3.0)


@pytest.fixture
def base_date() -> datetime.date:
    return datetime.date(2027, 2, 15)


def test_scenario_1_one_cook_one_valid_booking(scheduler: SlotChefScheduler, base_date: datetime.date) -> None:
    cook = CookInput(
        id="cook_1",
        skills={"basic_breakfast"},
        working_windows=[TimeWindow(420, 660)],  # 07:00 to 11:00
    )
    booking = BookingInput(
        id="book_1",
        household_id="h1",
        society_id="soc_1",
        earliest_start_minute=450,
        latest_finish_minute=540,
        duration_minutes=45,
        service_date=base_date,
        required_skills={"basic_breakfast"},
    )
    snapshot = SchedulingSnapshot("snap_1", "soc_1", base_date, [booking], [cook])
    result = scheduler.solve(snapshot)

    assert result.status == SolverStatus.OPTIMAL
    assert len(result.assignments) == 1
    assert len(result.unassigned) == 0
    assignment = result.assignments[0]
    assert assignment.cook_id == "cook_1"
    assert assignment.duration_minutes == 45
    assert assignment.start_minute >= 450
    assert assignment.end_minute <= 540


def test_scenario_2_one_cook_two_overlapping_bookings(scheduler: SlotChefScheduler) -> None:
    # Alexa 7:30 AM conflict: 2 requests of 45m in the same 60m window (450..510)
    # Total required = 45 + 5 (buffer) + 45 = 95m > 60m window.
    # Exactly one can be assigned; the other MUST remain unassigned.
    snapshot = make_alexa_conflict_scenario(allow_household_b_extension=False, second_cook_available=False)
    result = scheduler.solve(snapshot)

    assert result.status == SolverStatus.OPTIMAL
    assert len(result.assignments) == 1
    assert len(result.unassigned) == 1
    assert result.unassigned[0].primary_reason == ReasonCode.TIME_WINDOW_CONFLICT


def test_scenario_3_two_cooks_two_overlapping_bookings(scheduler: SlotChefScheduler) -> None:
    # Same overlapping requests, but now Ben is also available
    snapshot = make_alexa_conflict_scenario(allow_household_b_extension=False, second_cook_available=True)
    result = scheduler.solve(snapshot)

    assert result.status == SolverStatus.OPTIMAL
    assert len(result.assignments) == 2
    assert len(result.unassigned) == 0
    assigned_cook_ids = {a.cook_id for a in result.assignments}
    assert assigned_cook_ids == {"cook_alexa", "cook_ben"}


def test_scenario_4_alexa_conflict_with_wider_window(scheduler: SlotChefScheduler) -> None:
    # If Household B allows finish up to 9:30 AM (570), Alexa can do both sequentially:
    # A: 7:30-8:15 (450..495)
    # Transition: 5 mins (495..500)
    # B: 8:20-9:05 (500..545 <= 570)
    snapshot = make_alexa_conflict_scenario(allow_household_b_extension=True, second_cook_available=False)
    result = scheduler.solve(snapshot)

    assert result.status == SolverStatus.OPTIMAL
    assert len(result.assignments) == 2
    assert len(result.unassigned) == 0

    sorted_a = sorted(result.assignments, key=lambda x: x.start_minute)
    first, second = sorted_a[0], sorted_a[1]
    assert first.end_minute + 5 <= second.start_minute


def test_scenario_5_cook_lacks_required_skill(scheduler: SlotChefScheduler, base_date: datetime.date) -> None:
    cook = CookInput(
        id="cook_1",
        skills={"basic_breakfast"},  # Lacks "gourmet_dessert"
        working_windows=[TimeWindow(420, 660)],
    )
    booking = BookingInput(
        id="book_1",
        household_id="h1",
        society_id="soc_1",
        earliest_start_minute=450,
        latest_finish_minute=540,
        duration_minutes=45,
        service_date=base_date,
        required_skills={"gourmet_dessert"},
    )
    snapshot = SchedulingSnapshot("snap_skill", "soc_1", base_date, [booking], [cook])
    result = scheduler.solve(snapshot)

    assert len(result.assignments) == 0
    assert len(result.unassigned) == 1
    assert result.unassigned[0].primary_reason == ReasonCode.NO_SKILL_MATCH


def test_scenario_6_cook_on_leave(scheduler: SlotChefScheduler, base_date: datetime.date) -> None:
    cook = CookInput(
        id="cook_1",
        skills={"basic_breakfast"},
        working_windows=[TimeWindow(420, 660)],
        leaves=[LeavePeriod(start_date=base_date, end_date=base_date, status="approved")],
    )
    booking = BookingInput(
        id="book_1",
        household_id="h1",
        society_id="soc_1",
        earliest_start_minute=450,
        latest_finish_minute=540,
        duration_minutes=45,
        service_date=base_date,
        required_skills={"basic_breakfast"},
    )
    snapshot = SchedulingSnapshot("snap_leave", "soc_1", base_date, [booking], [cook])
    result = scheduler.solve(snapshot)

    assert len(result.assignments) == 0
    assert len(result.unassigned) == 1
    assert result.unassigned[0].primary_reason == ReasonCode.COOK_ON_LEAVE


def test_scenario_7_booking_outside_working_hours(scheduler: SlotChefScheduler, base_date: datetime.date) -> None:
    cook = CookInput(
        id="cook_1",
        skills={"basic_breakfast"},
        working_windows=[TimeWindow(420, 540)],  # 07:00 to 09:00 (ends at 540)
    )
    booking = BookingInput(
        id="book_1",
        household_id="h1",
        society_id="soc_1",
        earliest_start_minute=600,  # 10:00 to 11:00
        latest_finish_minute=660,
        duration_minutes=45,
        service_date=base_date,
        required_skills={"basic_breakfast"},
    )
    snapshot = SchedulingSnapshot("snap_hours", "soc_1", base_date, [booking], [cook])
    result = scheduler.solve(snapshot)

    assert len(result.assignments) == 0
    assert len(result.unassigned) == 1
    assert result.unassigned[0].primary_reason == ReasonCode.OUTSIDE_WORKING_HOURS


def test_scenario_8_booking_overlaps_protected_break(scheduler: SlotChefScheduler, base_date: datetime.date) -> None:
    cook = CookInput(
        id="cook_1",
        skills={"basic_breakfast"},
        working_windows=[TimeWindow(420, 660)],  # 07:00 to 11:00
        breaks=[BreakInterval(start_minute=460, end_minute=500)],  # Protected break 07:40-08:20
    )
    # Booking window is 07:30 to 08:30 (450..510) for 45 mins.
    # Any 45-min interval in [450, 510] must overlap [460, 500], so it must be rejected!
    booking = BookingInput(
        id="book_1",
        household_id="h1",
        society_id="soc_1",
        earliest_start_minute=450,
        latest_finish_minute=510,
        duration_minutes=45,
        service_date=base_date,
        required_skills={"basic_breakfast"},
    )
    snapshot = SchedulingSnapshot("snap_break", "soc_1", base_date, [booking], [cook])
    result = scheduler.solve(snapshot)

    assert len(result.assignments) == 0
    assert len(result.unassigned) == 1


def test_scenario_9_directional_transition_buffer_enforced(scheduler: SlotChefScheduler, base_date: datetime.date) -> None:
    # Cook is available 07:00 to 10:00 (420..600).
    # Booking 1: 07:00 to 08:00 (420..480), 45m duration.
    # Booking 2: 08:00 to 09:00 (480..540), 45m duration.
    # Between location A and B, travel time is 30 minutes!
    # If B1 finishes at 465, 465 + 30 = 495 > 480.
    # With a 30m travel time, second booking must start at or after 495.
    cook = CookInput(
        id="cook_1",
        skills={"basic_breakfast"},
        working_windows=[TimeWindow(420, 660)],
    )
    b1 = BookingInput(
        id="b1",
        household_id="h1",
        society_id="soc_1",
        earliest_start_minute=420,
        latest_finish_minute=480,
        duration_minutes=45,
        service_date=base_date,
        required_skills={"basic_breakfast"},
        location_id="loc_alpha",
    )
    b2 = BookingInput(
        id="b2",
        household_id="h2",
        society_id="soc_1",
        earliest_start_minute=480,
        latest_finish_minute=560,
        duration_minutes=45,
        service_date=base_date,
        required_skills={"basic_breakfast"},
        location_id="loc_beta",
    )
    travel = {("loc_alpha", "loc_beta"): 30, ("loc_beta", "loc_alpha"): 30}
    snapshot = SchedulingSnapshot("snap_travel", "soc_1", base_date, [b1, b2], [cook], travel_matrix=travel)
    result = scheduler.solve(snapshot)

    assert result.status == SolverStatus.OPTIMAL
    assert len(result.assignments) == 2
    by_id = {a.booking_id: a for a in result.assignments}
    # b2 start must be >= b1 end + 30
    assert by_id["b2"].start_minute >= by_id["b1"].end_minute + 30


def test_scenario_10_daily_workload_limit_reached(scheduler: SlotChefScheduler, base_date: datetime.date) -> None:
    cook = CookInput(
        id="cook_1",
        skills={"basic_breakfast"},
        working_windows=[TimeWindow(420, 660)],
        max_daily_visits=1,  # Only 1 visit permitted
    )
    b1 = BookingInput(
        id="b1",
        household_id="h1",
        society_id="soc_1",
        earliest_start_minute=420,
        latest_finish_minute=500,
        duration_minutes=45,
        service_date=base_date,
        required_skills={"basic_breakfast"},
    )
    b2 = BookingInput(
        id="b2",
        household_id="h2",
        society_id="soc_1",
        earliest_start_minute=510,
        latest_finish_minute=600,
        duration_minutes=45,
        service_date=base_date,
        required_skills={"basic_breakfast"},
    )
    snapshot = SchedulingSnapshot("snap_limit", "soc_1", base_date, [b1, b2], [cook])
    result = scheduler.solve(snapshot)

    assert len(result.assignments) == 1
    assert len(result.unassigned) == 1


def test_scenario_11_all_cooks_unavailable_returns_unassigned(scheduler: SlotChefScheduler, base_date: datetime.date) -> None:
    booking = BookingInput(
        id="b1",
        household_id="h1",
        society_id="soc_1",
        earliest_start_minute=420,
        latest_finish_minute=500,
        duration_minutes=45,
        service_date=base_date,
    )
    snapshot = SchedulingSnapshot("snap_nocook", "soc_1", base_date, [booking], [])
    result = scheduler.solve(snapshot)

    assert len(result.assignments) == 0
    assert len(result.unassigned) == 1
    assert result.unassigned[0].primary_reason == ReasonCode.NO_FEASIBLE_COOK

