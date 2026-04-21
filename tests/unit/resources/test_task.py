import httpx
from reclaim_sdk.resources.task import Task


def test_prioritize_by_due_does_not_raise_attribute_error(client, mock_api):
    mock_api.patch("/api/tasks/reindex-by-due").mock(
        return_value=httpx.Response(200, json=[])
    )
    # Must not raise AttributeError — the old code did cls._client which is unset
    Task.prioritize_by_due()

from reclaim_sdk.enums import PriorityLevel, TaskSource, EventSubType


def test_task_has_new_required_fields(client):
    t = Task(
        title="hello",
        priority=PriorityLevel.P3,
        taskSource=TaskSource.RECLAIM,
        readOnlyFields=[],
        sortKey=1.0,
        prioritizableType="TASK",
        type="TASK",
    )
    assert t.task_source == TaskSource.RECLAIM
    assert t.read_only_fields == []
    assert t.sort_key == 1.0
    assert t.type == "TASK"


def test_task_priority_uses_priority_level_enum(client):
    t = Task(title="x", priority=PriorityLevel.P1)
    assert t.priority == PriorityLevel.P1


def test_task_event_sub_type_is_enum(client):
    t = Task(title="x", eventSubType=EventSubType.FOCUS)
    assert t.event_sub_type == EventSubType.FOCUS


def test_task_priority_old_enum_removed():
    # TaskPriority must no longer exist (breaking)
    import reclaim_sdk.resources.task as tm
    assert not hasattr(tm, "TaskPriority")


from datetime import datetime


def test_create_at_time_posts_to_at_time_endpoint(client, mock_api):
    route = mock_api.post("/api/tasks/at-time").mock(
        return_value=httpx.Response(200, json={"id": 99, "title": "at-time", "type": "TASK"})
    )
    draft = Task(title="at-time", priority=PriorityLevel.P3, taskSource=TaskSource.RECLAIM)
    result = Task.create_at_time(draft, datetime(2026, 5, 1, 9, 0))
    assert route.called
    params = dict(route.calls.last.request.url.params)
    assert "startTime" in params
    assert isinstance(result, Task)
    assert result.id == 99


def test_find_min_index_returns_float(client, mock_api):
    mock_api.get("/api/users/current").mock(return_value=httpx.Response(200, json={"id": 1}))
    mock_api.get("/api/tasks/min-index").mock(return_value=httpx.Response(200, json=0.5))
    result = Task.find_min_index()
    assert result == 0.5


def test_find_min_index_handles_null(client, mock_api):
    mock_api.get("/api/users/current").mock(return_value=httpx.Response(200, json={"id": 1}))
    mock_api.get("/api/tasks/min-index").mock(return_value=httpx.Response(200, json=None))
    assert Task.find_min_index() is None


from reclaim_sdk.resources.task import TaskPatch


def test_task_patch_model_aliases():
    p = TaskPatch(taskId=1, patch={"title": "new"})
    dumped = p.model_dump(by_alias=True)
    assert dumped["taskId"] == 1
    assert dumped["patch"] == {"title": "new"}


def test_batch_patch_sends_array(client, mock_api):
    route = mock_api.patch("/api/tasks/batch").mock(
        return_value=httpx.Response(200, json={})
    )
    patches = [TaskPatch(taskId=1, patch={"title": "a"}),
               TaskPatch(taskId=2, patch={"title": "b"})]
    Task.batch_patch(patches)
    body = route.calls.last.request.content
    assert b'"taskId":1' in body and b'"taskId":2' in body


def test_batch_delete_sends_array(client, mock_api):
    route = mock_api.delete("/api/tasks/batch").mock(
        return_value=httpx.Response(200, json={})
    )
    Task.batch_delete([TaskPatch(taskId=5, patch={})])
    assert route.called


def test_batch_archive_sends_array(client, mock_api):
    route = mock_api.patch("/api/tasks/batch/archive").mock(
        return_value=httpx.Response(200, json={})
    )
    Task.batch_archive([TaskPatch(taskId=5, patch={})])
    assert route.called


def test_register_interest_posts(client, mock_api):
    route = mock_api.post("/api/tasks/interest").mock(
        return_value=httpx.Response(200, json=None)
    )
    Task.register_interest({"id": 7})
    body = route.calls.last.request.content
    assert b'"user"' in body and b'"id":7' in body
