from typing import Optional
from pydantic import BaseModel, Field
from reclaim_sdk.client import ReclaimClient


class ChangeLogEntryView(BaseModel):
    id: Optional[int] = Field(None)
    changed_at: Optional[str] = Field(None, alias="changedAt")
    reclaim_event_type: Optional[str] = Field(None, alias="reclaimEventType")
    assignment_id: Optional[int] = Field(None, alias="assignmentId")
    event_id: Optional[str] = Field(None, alias="eventId")
    organizer_id: Optional[str] = Field(None, alias="organizerId")
    actor_id: Optional[str] = Field(None, alias="actorId")
    reason: Optional[str] = Field(None)

    model_config = {"populate_by_name": True, "extra": "allow"}


def _client_or_default(client):
    return client or ReclaimClient()


class Changelog:
    @staticmethod
    def tasks(task_ids: list[int], client=None) -> list[ChangeLogEntryView]:
        data = _client_or_default(client).get(
            "/api/changelog/tasks", params={"taskIds": task_ids}
        )
        return [ChangeLogEntryView.model_validate(x) for x in (data or [])]

    @staticmethod
    def events(event_ids: list[str], client=None) -> list[ChangeLogEntryView]:
        data = _client_or_default(client).get(
            "/api/changelog/events", params={"eventIds": event_ids}
        )
        return [ChangeLogEntryView.model_validate(x) for x in (data or [])]

    @staticmethod
    def smart_habits(ids: list[int], client=None) -> list[ChangeLogEntryView]:
        data = _client_or_default(client).get(
            "/api/changelog/smart-habits", params={"ids": ids}
        )
        return [ChangeLogEntryView.model_validate(x) for x in (data or [])]

    @staticmethod
    def smart_meetings(ids: list[int], client=None) -> list[ChangeLogEntryView]:
        data = _client_or_default(client).get(
            "/api/changelog/smart-meetings", params={"ids": ids}
        )
        return [ChangeLogEntryView.model_validate(x) for x in (data or [])]

    @staticmethod
    def scheduling_links(ids: list[str], client=None) -> list[ChangeLogEntryView]:
        data = _client_or_default(client).get(
            "/api/changelog/scheduling-links", params={"ids": ids}
        )
        return [ChangeLogEntryView.model_validate(x) for x in (data or [])]

    @staticmethod
    def all(client=None) -> list[ChangeLogEntryView]:
        data = _client_or_default(client).get("/api/changelog")
        return [ChangeLogEntryView.model_validate(x) for x in (data or [])]
