"""Time conversion and arithmetic utilities for scheduling (minutes from midnight)."""

from __future__ import annotations

import datetime
from zoneinfo import ZoneInfo


def parse_time_to_minutes(val: str | datetime.time) -> int:
    """Convert 'HH:MM' or datetime.time into integer minutes from midnight (0..1440)."""
    if isinstance(val, str):
        parts = val.strip().split(":")
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        return hour * 60 + minute
    if isinstance(val, datetime.time):
        return val.hour * 60 + val.minute
    raise TypeError(f"Unsupported time type: {type(val)}")


def minutes_to_time_str(minutes: int) -> str:
    """Convert integer minutes from midnight to 'HH:MM' 24-hour string."""
    if minutes < 0 or minutes > 1440:
        raise ValueError(f"Minutes {minutes} out of day range [0, 1440]")
    hours = (minutes // 60) % 24
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"


def minutes_to_time(minutes: int) -> datetime.time:
    """Convert integer minutes from midnight to datetime.time."""
    hours = (minutes // 60) % 24
    mins = minutes % 60
    return datetime.time(hour=hours, minute=mins)


def minutes_to_datetime(
    service_date: datetime.date,
    minutes: int,
    tz: str | datetime.tzinfo = "UTC",
) -> datetime.datetime:
    """Convert service date + integer minute to timezone-aware UTC datetime."""
    tzone = ZoneInfo(tz) if isinstance(tz, str) else tz
    t = minutes_to_time(minutes)
    local_dt = datetime.datetime.combine(service_date, t, tzinfo=tzone)
    return local_dt.astimezone(datetime.UTC)


def datetime_to_minutes(
    dt: datetime.datetime,
    target_tz: str | datetime.tzinfo = "UTC",
) -> int:
    """Convert timezone-aware datetime to integer minutes from midnight in target timezone."""
    tzone = ZoneInfo(target_tz) if isinstance(target_tz, str) else target_tz
    local_dt = dt.astimezone(tzone)
    return local_dt.hour * 60 + local_dt.minute
