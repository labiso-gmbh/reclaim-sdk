import json
from reclaim_sdk.webhooks.payloads import (
    parse_webhook_payload, TaskWebhookEvent, HabitWebhookEvent,
)


def test_parse_task_created_payload(client):
    raw = json.dumps({
        "eventId": "evt-1",
        "type": "task.created",
        "created": "2026-04-21T10:00:00Z",
        "task": {
            "id": 1, "title": "hello", "type": "TASK",
            "priority": "P3", "taskSource": "RECLAIM",
            "readOnlyFields": [], "sortKey": 1.0,
            "prioritizableType": "TASK",
            "eventCategory": "WORK", "eventSubType": "FOCUS",
            "onDeck": False, "atRisk": False, "deleted": False,
            "adjusted": False, "deferred": False, "alwaysPrivate": False,
            "status": "NEW", "index": 0.0,
            "timeChunksRequired": 4, "minChunkSize": 1, "maxChunkSize": 4,
            "timeChunksSpent": 0, "timeChunksRemaining": 4,
            "notes": "", "timeSchemeId": "",
            "created": "2026-04-21T10:00:00Z", "updated": "2026-04-21T10:00:00Z",
        },
    })
    evt = parse_webhook_payload(raw)
    assert isinstance(evt, TaskWebhookEvent)
    assert evt.type == "task.created"
    assert evt.task.id == 1


def test_parse_habit_updated_payload(client):
    raw = json.dumps({
        "eventId": "evt-2",
        "type": "habit.updated",
        "created": "2026-04-21T10:00:00Z",
        "habit": {"id": 99, "title": "Run", "type": "CUSTOM_DAILY"},
    })
    evt = parse_webhook_payload(raw)
    assert isinstance(evt, HabitWebhookEvent)
    assert evt.habit.id == 99


def test_parse_unknown_type_raises(client):
    import pydantic
    raw = json.dumps({"eventId": "e", "type": "unknown.thing", "created": "2026-04-21T10:00:00Z"})
    try:
        parse_webhook_payload(raw)
    except pydantic.ValidationError:
        return
    assert False, "expected ValidationError"
