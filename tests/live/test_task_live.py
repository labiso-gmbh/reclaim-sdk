import pytest
from datetime import datetime, timedelta, timezone
from reclaim_sdk.resources.task import Task
from reclaim_sdk.enums import PriorityLevel, TaskSource, SnoozeOption


pytestmark = pytest.mark.live


def test_task_full_lifecycle(live_client, tracked_ids, prefix):
    task = Task(
        title=f"{prefix} lifecycle",
        priority=PriorityLevel.P3,
        taskSource=TaskSource.RECLAIM,
    )
    task.duration = 1.0
    task.save()
    tracked_ids["tasks"].append(task.id)
    assert task.id is not None
    assert task.title.startswith(prefix)

    # update
    task.notes = "updated"
    task.save()
    task.refresh()
    assert task.notes == "updated"

    # planner actions
    task.start()
    task.stop()
    task.snooze(SnoozeOption.ONE_HOUR)
    task.clear_snooze()
    task.mark_complete()
    task.mark_incomplete()

    # found in list
    listed = [t.id for t in Task.list()]
    assert task.id in listed
