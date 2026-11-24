"""Unit tests for time conversion utilities."""

from __future__ import annotations

import datetime

import pytest

from slotchef_optimizer.utils.time_utils import (
    datetime_to_minutes,
    minutes_to_datetime,
    minutes_to_time_str,
    parse_time_to_minutes,
)


def test_parse_time_to_minutes() -> None:
    assert parse_time_to_minutes("07:30") == 450
    assert parse_time_to_minutes("00:00") == 0
    assert parse_time_to_minutes("23:59") == 1439
    assert parse_time_to_minutes(datetime.time(8, 15)) == 495


def test_minutes_to_time_str() -> None:
    assert minutes_to_time_str(450) == "07:30"
    assert minutes_to_time_str(0) == "00:00"
    assert minutes_to_time_str(1439) == "23:59"
    with pytest.raises(ValueError):
        minutes_to_time_str(-5)
    with pytest.raises(ValueError):
        minutes_to_time_str(1441)


def test_minutes_to_datetime_and_roundtrip() -> None:
    d = datetime.date(2027, 2, 15)
    dt_utc = minutes_to_datetime(d, 450, tz="UTC")
    assert dt_utc.year == 2027
    assert dt_utc.month == 2
    assert dt_utc.day == 15
    assert dt_utc.hour == 7
    assert dt_utc.minute == 30
    assert dt_utc.tzinfo == datetime.UTC

    # Roundtrip
    m = datetime_to_minutes(dt_utc, target_tz="UTC")
    assert m == 450
