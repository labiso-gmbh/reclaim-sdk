"""Live time-scheme tests.

Hits real ``api.app.reclaim.ai``. Skipped unless ``RECLAIM_LIVE_TEST=1`` and
``RECLAIM_TOKEN`` are set. Each create-test cleans up after itself.
"""

from datetime import time

import pytest

from reclaim_sdk.enums import PolicyType, TimeSchemeFeature, Weekday
from reclaim_sdk.resources.hours import (
    DayIntervals,
    Hours,
    Interval,
    TimeSchemePolicy,
)

pytestmark = pytest.mark.live


def test_hours_list_returns_schemes(live_client):
    schemes = Hours.list()
    assert isinstance(schemes, list)
    # every account ships with built-in Work / Personal / Meeting schemes
    assert len(schemes) >= 1


def test_hours_full_crud_round_trip(live_client, prefix):
    """create → patch → get → delete a custom 9-to-5 Mon-Fri scheme."""
    workday = DayIntervals(intervals=[Interval(start=time(9, 0), end=time(17, 0))])
    scheme = Hours(
        title=f"{prefix} CRUD Hours",
        description="Created by SDK live test",
        task_category="WORK",
        policy_type=PolicyType.CUSTOM,
        policy=TimeSchemePolicy(
            day_hours={
                Weekday.MONDAY: workday,
                Weekday.TUESDAY: workday,
                Weekday.WEDNESDAY: workday,
                Weekday.THURSDAY: workday,
                Weekday.FRIDAY: workday,
            }
        ),
        features=[
            TimeSchemeFeature.TASK_ASSIGNMENT,
            TimeSchemeFeature.HABIT_ASSIGNMENT,
        ],
    )

    try:
        # CREATE
        scheme.save()
        assert scheme.id, "server must assign an id on create"
        assert scheme.policy_type == PolicyType.CUSTOM
        assert Weekday.MONDAY in scheme.policy.day_hours

        # GET
        fetched = Hours.get(scheme.id)
        assert fetched.title == scheme.title
        assert fetched.policy.day_hours[Weekday.FRIDAY].intervals[0].end == time(17, 0)

        # PATCH
        fetched.description = "Updated by SDK live test"
        fetched.save()
        re_fetched = Hours.get(scheme.id)
        assert re_fetched.description == "Updated by SDK live test"

        # LIST contains it
        all_schemes = Hours.list()
        assert any(s.id == scheme.id for s in all_schemes)
    finally:
        # DELETE — best-effort cleanup even if assertions above failed
        if scheme.id:
            try:
                Hours.get(scheme.id).delete()
            except Exception:
                pass

    # confirm gone
    remaining = [s for s in Hours.list() if s.id == scheme.id]
    assert remaining == [], "scheme must be removed after delete"
