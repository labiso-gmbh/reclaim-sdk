import pytest
from reclaim_sdk.resources.habit import DailyHabit

pytestmark = pytest.mark.live


def test_habit_lifecycle(live_client, tracked_ids, prefix):
    h = DailyHabit(title=f"{prefix} habit")
    h.save()
    tracked_ids["habits"].append(h.id)
    h.toggle(enable=False)
    h.toggle(enable=True)
