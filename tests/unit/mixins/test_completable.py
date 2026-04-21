import httpx
from reclaim_sdk.resources.task import Task
from reclaim_sdk.enums import PriorityLevel, TaskSource


def test_mark_complete_posts_done(client, mock_api):
    mock_api.post("/api/planner/done/task/42").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 42, "type": "TASK"}})
    )
    t = Task(id=42, title="x", priority=PriorityLevel.P3, taskSource=TaskSource.RECLAIM)
    t.mark_complete()


def test_mark_incomplete_posts_unarchive(client, mock_api):
    mock_api.post("/api/planner/unarchive/task/42").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 42, "type": "TASK"}})
    )
    t = Task(id=42, title="x", priority=PriorityLevel.P3, taskSource=TaskSource.RECLAIM)
    t.mark_incomplete()
