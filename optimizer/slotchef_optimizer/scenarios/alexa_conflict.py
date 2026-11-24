"""Deterministic test scenario builders, including Alexa's 7:30 AM conflict."""

from __future__ import annotations

import datetime

from slotchef_optimizer.models.domain import (
    BookingInput,
    CookInput,
    SchedulingSnapshot,
    TimeWindow,
)


def make_alexa_conflict_scenario(
    allow_household_b_extension: bool = False,
    second_cook_available: bool = False,
) -> SchedulingSnapshot:
    """Build Alexa's 7:30 AM conflict scenario (Section 3.1).

    Household A: 7:30-8:30 AM (450..510), 45 mins duration.
    Household B: 7:30-8:30 AM (450..510, or 450..570 if extended), 45 mins duration.
    Alexa: 7:00-11:00 AM (420..660), 5-minute transition buffer.
    """
    service_date = datetime.date(2027, 2, 15)

    alexa = CookInput(
        id="cook_alexa",
        name="Alexa",
        is_active=True,
        is_verified=True,
        authorized_societies={"soc_palm_grove"},
        skills={"basic_breakfast"},
        working_windows=[TimeWindow(start_minute=420, end_minute=660)],  # 07:00 to 11:00
        default_buffer_minutes=5,
    )
    cooks = [alexa]

    if second_cook_available:
        ben = CookInput(
            id="cook_ben",
            name="Ben",
            is_active=True,
            is_verified=True,
            authorized_societies={"soc_palm_grove"},
            skills={"basic_breakfast"},
            working_windows=[TimeWindow(start_minute=420, end_minute=660)],
            default_buffer_minutes=5,
        )
        cooks.append(ben)

    booking_a = BookingInput(
        id="book_h_a",
        household_id="house_a",
        society_id="soc_palm_grove",
        earliest_start_minute=450,  # 07:30
        latest_finish_minute=510,  # 08:30
        duration_minutes=45,
        service_date=service_date,
        required_skills={"basic_breakfast"},
        location_id="bldg_1",
    )

    finish_b = 570 if allow_household_b_extension else 510  # 09:30 or 08:30
    booking_b = BookingInput(
        id="book_h_b",
        household_id="house_b",
        society_id="soc_palm_grove",
        earliest_start_minute=450,  # 07:30
        latest_finish_minute=finish_b,
        duration_minutes=45,
        service_date=service_date,
        required_skills={"basic_breakfast"},
        location_id="bldg_1",
    )

    return SchedulingSnapshot(
        snapshot_version="v1-alexa-test",
        society_id="soc_palm_grove",
        service_date=service_date,
        bookings=[booking_a, booking_b],
        cooks=cooks,
        default_transition_minutes=5,
    )
