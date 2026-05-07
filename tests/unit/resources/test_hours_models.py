from datetime import time

from reclaim_sdk.resources.hours import (
    Interval, DayIntervals, TimeSchemePolicy,
)
from reclaim_sdk.enums import Weekday


def test_interval_parses_hms_strings():
    interval = Interval(start="09:00:00", end="17:30:00")
    assert interval.start == time(9, 0, 0)
    assert interval.end == time(17, 30, 0)


def test_interval_serializes_to_hms_strings():
    interval = Interval(start=time(9, 0), end=time(17, 0))
    dumped = interval.model_dump(mode="json")
    assert dumped["start"] == "09:00:00"
    assert dumped["end"] == "17:00:00"


def test_interval_ignores_server_only_duration_field():
    """Server returns ``duration`` (seconds) on each interval; SDK accepts
    and round-trips it without breaking parsing."""
    interval = Interval.model_validate({
        "start": "09:00:00", "end": "17:00:00", "duration": 28800.0,
    })
    assert interval.start == time(9, 0)


def test_day_intervals_holds_list_of_intervals():
    day = DayIntervals(intervals=[
        Interval(start=time(9, 0), end=time(12, 0)),
        Interval(start=time(13, 0), end=time(17, 0)),
    ])
    assert len(day.intervals) == 2


def test_day_intervals_accepts_server_extras():
    """Server adds ``startOfDay`` / ``endOfDay`` next to ``intervals`` — must
    not reject them."""
    day = DayIntervals.model_validate({
        "intervals": [{"start": "09:00:00", "end": "17:00:00"}],
        "startOfDay": "09:00:00",
        "endOfDay": "17:00:00",
    })
    assert day.start_of_day == time(9, 0)
    assert day.end_of_day == time(17, 0)


def test_time_scheme_policy_keys_day_hours_by_weekday():
    policy = TimeSchemePolicy.model_validate({
        "dayHours": {
            "MONDAY": {"intervals": [{"start": "09:00:00", "end": "17:00:00"}]},
            "FRIDAY": {"intervals": [{"start": "10:00:00", "end": "14:00:00"}]},
        },
    })
    assert Weekday.MONDAY in policy.day_hours
    assert Weekday.FRIDAY in policy.day_hours
    assert policy.day_hours[Weekday.FRIDAY].intervals[0].end == time(14, 0)


def test_time_scheme_policy_serializes_with_camel_case():
    policy = TimeSchemePolicy(day_hours={
        Weekday.MONDAY: DayIntervals(intervals=[
            Interval(start=time(9, 0), end=time(17, 0)),
        ]),
    })
    dumped = policy.model_dump(mode="json", by_alias=True, exclude_none=True)
    assert "dayHours" in dumped
    assert "MONDAY" in dumped["dayHours"]
    assert dumped["dayHours"]["MONDAY"]["intervals"][0] == {
        "start": "09:00:00", "end": "17:00:00",
    }
