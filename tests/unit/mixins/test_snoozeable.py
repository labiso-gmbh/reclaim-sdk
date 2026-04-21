import httpx
from datetime import datetime
from reclaim_sdk.resources.task import Task
from reclaim_sdk.enums import SnoozeOption, PriorityLevel, TaskSource


def test_task_snooze_posts_to_snooze_endpoint(client, mock_api):
    route = mock_api.post("/api/planner/task/42/snooze").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 42, "type": "TASK"}})
    )
    t = Task(id=42, title="x", priority=PriorityLevel.P3)
    t.snooze(SnoozeOption.FROM_NOW_1H)
    assert route.called
    params = dict(route.calls.last.request.url.params)
    assert params.get("snoozeOption") == "FROM_NOW_1H"


def test_task_clear_snooze_posts(client, mock_api):
    route = mock_api.post("/api/planner/task/42/clear-snooze").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 42, "type": "TASK"}})
    )
    t = Task(id=42, title="x", priority=PriorityLevel.P3)
    t.clear_snooze()
    assert route.called
