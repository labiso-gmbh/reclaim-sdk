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
