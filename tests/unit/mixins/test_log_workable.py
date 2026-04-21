import httpx
from datetime import datetime, timezone
from reclaim_sdk.resources.task import Task
from reclaim_sdk.enums import PriorityLevel, TaskSource


def test_log_work_sends_minutes_and_zulu_end(client, mock_api):
    route = mock_api.post("/api/planner/log-work/task/42").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 42, "type": "TASK"}})
    )
    t = Task(id=42, title="x", priority=PriorityLevel.P3)
    t.log_work(60, datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc))
    params = dict(route.calls.last.request.url.params)
    assert params["minutes"] == "60"
    assert params["end"].endswith("Z")
    # existing truncation: isoformat()[:-9] + "Z"
    # datetime without microseconds yields YYYY-MM-DDTHH:MMZ (17 chars)
    assert len(params["end"]) == 17
