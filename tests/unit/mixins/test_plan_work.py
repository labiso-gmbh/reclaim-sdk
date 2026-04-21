import httpx
from datetime import datetime, timezone
from reclaim_sdk.resources.task import Task
from reclaim_sdk.enums import PriorityLevel, TaskSource


def test_plan_work_posts_with_datetime_and_duration(client, mock_api):
    route = mock_api.post("/api/planner/plan-work/task/42").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 42, "type": "TASK"}})
    )
    t = Task(id=42, title="x", priority=PriorityLevel.P3, taskSource=TaskSource.RECLAIM)
    t.plan_work(datetime(2026, 5, 1, 9, 0, tzinfo=timezone.utc), duration_minutes=60)
    params = dict(route.calls.last.request.url.params)
    assert "dateTime" in params
    assert params["durationMinutes"] == "60"
