from datetime import datetime
from typing import Annotated, Literal, Union
from pydantic import BaseModel, Field, TypeAdapter
from reclaim_sdk.resources.task import Task
from reclaim_sdk.resources.habit import DailyHabit


class _Base(BaseModel):
    event_id: str = Field(alias="eventId")
    created: datetime

    model_config = {"populate_by_name": True}


class TaskWebhookEvent(_Base):
    type: Literal["task.created", "task.updated", "task.completed", "task.deleted"]
    task: Task


class HabitWebhookEvent(_Base):
    type: Literal["habit.created", "habit.updated", "habit.deleted"]
    habit: DailyHabit


WebhookEvent = Annotated[
    Union[TaskWebhookEvent, HabitWebhookEvent],
    Field(discriminator="type"),
]

_adapter = TypeAdapter(WebhookEvent)


def parse_webhook_payload(raw: bytes | str) -> WebhookEvent:
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    return _adapter.validate_json(raw)
