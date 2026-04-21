import httpx
from reclaim_sdk.resources.task import Task
from reclaim_sdk.enums import PriorityLevel, TaskSource


def test_clear_exceptions_posts(client, mock_api):
    route = mock_api.post("/api/planner/clear-exceptions/task/42").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 42, "type": "TASK"}})
    )
    t = Task(id=42, title="x", priority=PriorityLevel.P3)
    t.clear_exceptions()
    assert route.called
