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
    # Millisecond-precision Zulu format: YYYY-MM-DDTHH:MM:SS.mmmZ (24 chars)
    assert len(params["end"]) == 24
    assert params["end"].endswith(".000Z")  # zero microseconds → .000


def test_log_work_zero_microsecond_keeps_seconds(client, mock_api):
    """Regression: zero-microsecond `end` must not lose seconds via [:-9] truncation."""
    route = mock_api.post("/api/planner/log-work/task/7").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 7, "type": "TASK"}})
    )
    t = Task(id=7, title="x", priority=PriorityLevel.P3)
    t.log_work(15, datetime(2026, 5, 1, 14, 30, 0, tzinfo=timezone.utc))
    end = dict(route.calls.last.request.url.params)["end"]
    # Correct shape: YYYY-MM-DDTHH:MM:SS.mmmZ (millisecond precision, 24 chars)
    assert end == "2026-05-01T14:30:00.000Z", f"unexpected end format: {end!r}"


def test_log_work_with_microseconds_truncates_to_millis(client, mock_api):
    """Microsecond-bearing inputs are truncated to millisecond precision."""
    route = mock_api.post("/api/planner/log-work/task/7").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 7, "type": "TASK"}})
    )
    t = Task(id=7, title="x", priority=PriorityLevel.P3)
    t.log_work(15, datetime(2026, 5, 1, 14, 30, 0, 123456, tzinfo=timezone.utc))
    end = dict(route.calls.last.request.url.params)["end"]
    assert end == "2026-05-01T14:30:00.123Z", f"unexpected end format: {end!r}"
