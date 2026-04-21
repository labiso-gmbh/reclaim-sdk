import httpx
from reclaim_sdk.resources.task import Task
from reclaim_sdk.enums import PriorityLevel, TaskSource


def test_task_start_hits_planner_start(client, mock_api):
    route = mock_api.post("/api/planner/start/task/42").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 42, "type": "TASK"}})
    )
    t = Task(id=42, title="x", priority=PriorityLevel.P3)
    t.start()
    assert route.called


def test_task_stop_hits_planner_stop(client, mock_api):
    route = mock_api.post("/api/planner/stop/task/42").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 42, "type": "TASK"}})
    )
    t = Task(id=42, title="x", priority=PriorityLevel.P3)
    t.stop()
    assert route.called
