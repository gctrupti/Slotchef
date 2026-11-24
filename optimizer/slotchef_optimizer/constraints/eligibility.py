"""Pre-solver eligibility filter for candidate cooks and reason tracking."""

from __future__ import annotations

import datetime

from slotchef_optimizer.explanations.reasons import ReasonCode
from slotchef_optimizer.models.domain import BookingInput, CookInput


def check_cook_eligibility_for_booking(
    cook: CookInput,
    booking: BookingInput,
    service_date: datetime.date,
) -> list[ReasonCode]:
    """Return a list of disqualifying ReasonCodes for a cook-booking pair, or empty if eligible."""
    reasons: list[ReasonCode] = []

    if not cook.is_active or not cook.is_verified:
        reasons.append(ReasonCode.INACTIVE_OR_UNVERIFIED)

    if cook.authorized_societies and booking.society_id not in cook.authorized_societies:
        reasons.append(ReasonCode.SOCIETY_MISMATCH)

    if booking.required_skills and not booking.required_skills.issubset(cook.skills):
        reasons.append(ReasonCode.NO_SKILL_MATCH)

    if any(leave.covers(service_date) for leave in cook.leaves):
        reasons.append(ReasonCode.COOK_ON_LEAVE)

    # Working hours check: does at least one window overlap and fit duration?
    window_fits = False
    for window in cook.working_windows:
        overlap_start = max(window.start_minute, booking.earliest_start_minute)
        overlap_end = min(window.end_minute, booking.latest_finish_minute)
        if overlap_end - overlap_start >= booking.duration_minutes:
            window_fits = True
            break
    if not window_fits:
        reasons.append(ReasonCode.OUTSIDE_WORKING_HOURS)

    # Existing workload count
    if len(cook.existing_commitments) >= cook.max_daily_visits:
        reasons.append(ReasonCode.DAILY_CAPACITY_REACHED)

    existing_minutes = sum(end - start for start, end in cook.existing_commitments)
    if existing_minutes + booking.duration_minutes > cook.max_daily_minutes:
        reasons.append(ReasonCode.DAILY_CAPACITY_REACHED)

    return reasons


def filter_eligible_candidates(
    cooks: list[CookInput],
    bookings: list[BookingInput],
    service_date: datetime.date,
) -> tuple[dict[str, list[CookInput]], dict[str, dict[str, list[ReasonCode]]]]:
    """Determine eligible cooks for each booking and collect exclusion reasons."""
    eligible_map: dict[str, list[CookInput]] = {}
    exclusions_map: dict[str, dict[str, list[ReasonCode]]] = {}

    for booking in bookings:
        eligible_for_b: list[CookInput] = []
        exclusions_for_b: dict[str, list[ReasonCode]] = {}

        for cook in cooks:
            disqualifications = check_cook_eligibility_for_booking(cook, booking, service_date)
            if disqualifications:
                exclusions_for_b[cook.id] = disqualifications
            else:
                eligible_for_b.append(cook)

        eligible_map[booking.id] = eligible_for_b
        exclusions_map[booking.id] = exclusions_for_b

    return eligible_map, exclusions_map

