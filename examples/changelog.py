"""Changelog read example."""

from reclaim_sdk.resources.task import Task
from reclaim_sdk.resources.changelog import Changelog

# Full changelog (recent events across tasks/habits/meetings)
for entry in Changelog.all():
    print(f"{entry.changed_at} {entry.reclaim_event_type} assignment={entry.assignment_id} reason={entry.reason}")

# Task-specific changelog — pass the ids you care about
tasks = Task.list()[:5]
if tasks:
    entries = Changelog.tasks([t.id for t in tasks])
    for e in entries:
        print(f"task {e.assignment_id}: {e.reclaim_event_type} ({e.reason})")
