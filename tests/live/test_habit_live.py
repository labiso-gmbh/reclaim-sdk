import pytest
from reclaim_sdk.resources.habit import DailyHabit

pytestmark = pytest.mark.live


def test_habit_list_parses_real_payloads(live_client):
    """Live habit creation returns 409 in many environments (scheduling conflicts,
    plan-tier limits, calendar ideal-time collisions). So we only exercise the
    read path against existing habits. This still proves:
    - GET /api/assist/habits/daily works
    - DailyHabit schema parses every real habit payload without ValidationError
    """
    habits = DailyHabit.list()
    assert isinstance(habits, list)
    for h in habits:
        assert h.id is not None
        assert h.type in (None, "CUSTOM_DAILY")
