from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone
from typing import Any, ClassVar, Optional
from reclaim_sdk.client import ReclaimClient
from reclaim_sdk.resources.base import BaseResource
from reclaim_sdk.enums import (
    PriorityLevel,
    EventCategory,
    EventColor,
    TaskStatus,
    TaskSource,
    EventSubType,
)
from reclaim_sdk.mixins.snoozeable import SnoozeableMixin


class Task(BaseResource, SnoozeableMixin):
    ENDPOINT: ClassVar[str] = "/api/tasks"
    USER_PARAM_REQUIRED: ClassVar[bool] = True
    _PLANNER_PATH_SEGMENT: ClassVar[str] = "task"

    title: Optional[str] = Field(None, description="Task title")
    notes: Optional[str] = Field(None, description="Task notes")
    event_category: EventCategory = Field(
        default=EventCategory.WORK, alias="eventCategory", description="Event category"
    )
    event_sub_type: Optional[EventSubType] = Field(
        None, alias="eventSubType", description="Event subtype"
    )
    time_scheme_id: Optional[str] = Field(
        None, alias="timeSchemeId", description="Time scheme ID (custom hours)"
    )
    time_chunks_required: Optional[int] = Field(
        None, alias="timeChunksRequired", description="Time chunks required"
    )
    min_chunk_size: Optional[int] = Field(
        None, alias="minChunkSize", description="Minimum chunk size"
    )
    max_chunk_size: Optional[int] = Field(
        None, alias="maxChunkSize", description="Maximum chunk size"
    )
    time_chunks_spent: Optional[int] = Field(
        None, alias="timeChunksSpent", description="Time chunks spent"
    )
    time_chunks_remaining: Optional[int] = Field(
        None, alias="timeChunksRemaining", description="Time chunks remaining"
    )
    priority: Optional[PriorityLevel] = Field(None, description="Task priority")
    on_deck: bool = Field(False, alias="onDeck", description="Task is on deck")
    at_risk: bool = Field(False, alias="atRisk", description="Task is at risk")
    deleted: bool = Field(False, alias="deleted", description="Task is deleted")
    adjusted: bool = Field(False, alias="adjusted", description="Task is adjusted")
    deferred: bool = Field(False, alias="deferred", description="Task is deferred")
    always_private: bool = Field(
        False, alias="alwaysPrivate", description="Task is always private"
    )
    task_source: TaskSource = Field(
        TaskSource.RECLAIM, alias="taskSource", description="Task origin"
    )
    read_only_fields: list[str] = Field(
        default_factory=list,
        alias="readOnlyFields",
        description="Server-enforced read-only fields",
    )
    sort_key: float = Field(0.0, alias="sortKey", description="Sort order key")
    prioritizable_type: str = Field(
        "TASK", alias="prioritizableType", description="Prioritizable polymorphic type"
    )
    type: str = Field("TASK", description="Discriminator for Task vs DailyHabit")
    status: Optional[TaskStatus] = Field(None, description="Task status")
    due: Optional[datetime] = Field(None, description="Due date")
    created: Optional[datetime] = Field(None, description="Created date")
    updated: Optional[datetime] = Field(None, description="Updated date")
    finished: Optional[datetime] = Field(None, description="Finished date")
    snooze_until: Optional[datetime] = Field(
        None, alias="snoozeUntil", description="Snooze until date"
    )
    index: Optional[float] = Field(None, description="Task index")
    event_color: EventColor = Field(None, alias="eventColor", description="Event color")

    @field_validator(
        "time_chunks_required", "min_chunk_size", "max_chunk_size", mode="before"
    )
    @classmethod
    def validate_chunks(cls, v):
        if v is not None:
            return int(v)
        return v

    @property
    def duration(self) -> Optional[float]:
        return self.time_chunks_required / 4 if self.time_chunks_required else None

    @duration.setter
    def duration(self, hours: float) -> None:
        self.time_chunks_required = int(hours * 4)

    @property
    def min_work_duration(self) -> Optional[float]:
        return self.min_chunk_size / 4 if self.min_chunk_size else None

    @min_work_duration.setter
    def min_work_duration(self, hours: float) -> None:
        self.min_chunk_size = int(hours * 4)

    @property
    def max_work_duration(self) -> Optional[float]:
        return self.max_chunk_size / 4 if self.max_chunk_size else None

    @max_work_duration.setter
    def max_work_duration(self, hours: float) -> None:
        self.max_chunk_size = int(hours * 4)

    @property
    def up_next(self) -> bool:
        return self.on_deck

    @up_next.setter
    def up_next(self, value: bool) -> None:
        self.on_deck = value

    def mark_complete(self) -> None:
        response = self._client.post(f"/api/planner/done/task/{self.id}")
        self.from_api_data(response["taskOrHabit"])

    def mark_incomplete(self) -> None:
        response = self._client.post(f"/api/planner/unarchive/task/{self.id}")
        self.from_api_data(response["taskOrHabit"])

    @classmethod
    def prioritize_by_due(cls, client: ReclaimClient = None) -> list["Task"]:
        if client is None:
            client = ReclaimClient()
        data = client.patch("/api/tasks/reindex-by-due")
        return [cls.from_api_data(item) for item in (data or [])]

    @classmethod
    def create_at_time(
        cls, task: "Task", start_time: datetime, client: ReclaimClient = None
    ) -> "Task":
        if client is None:
            client = ReclaimClient()
        params = {"startTime": start_time.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")}
        data = client.post(cls.ENDPOINT + "/at-time", params=params, json=task.to_api_data())
        # response shape: CreateTaskAtTimeView — contains the created task under "task" or is the task itself
        payload = data.get("task", data) if isinstance(data, dict) else data
        return cls.from_api_data(payload)

    @classmethod
    def find_min_index(cls, client: ReclaimClient = None) -> Optional[float]:
        if client is None:
            client = ReclaimClient()
        params = {"user": client.current_user().get("id")}
        return client.get(cls.ENDPOINT + "/min-index", params=params)

    @classmethod
    def batch_patch(cls, patches: list["TaskPatch"], client: ReclaimClient = None) -> dict:
        if client is None:
            client = ReclaimClient()
        body = [p.model_dump(by_alias=True, exclude_none=True) for p in patches]
        return client.patch(cls.ENDPOINT + "/batch", json=body)

    @classmethod
    def batch_delete(cls, patches: list["TaskPatch"], client: ReclaimClient = None) -> dict:
        if client is None:
            client = ReclaimClient()
        body = [p.model_dump(by_alias=True, exclude_none=True) for p in patches]
        return client.delete(cls.ENDPOINT + "/batch", json=body)

    @classmethod
    def batch_archive(cls, patches: list["TaskPatch"], client: ReclaimClient = None) -> dict:
        if client is None:
            client = ReclaimClient()
        body = [p.model_dump(by_alias=True, exclude_none=True) for p in patches]
        return client.patch(cls.ENDPOINT + "/batch/archive", json=body)

    @classmethod
    def register_interest(cls, user: dict, client: ReclaimClient = None) -> None:
        if client is None:
            client = ReclaimClient()
        client.post(cls.ENDPOINT + "/interest", json={"user": user})

    def prioritize(self) -> None:
        self._client.post(f"/api/planner/prioritize/task/{self.id}")
        self.refresh()

    def add_time(self, hours: float) -> None:
        minutes = int(hours * 60)
        rounded_minutes = round(minutes / 15) * 15
        response = self._client.post(
            f"/api/planner/add-time/task/{self.id}", params={"minutes": rounded_minutes}
        )
        self.from_api_data(response["taskOrHabit"])

    def clear_exceptions(self) -> None:
        response = self._client.post(f"/api/planner/clear-exceptions/task/{self.id}")
        self.from_api_data(response["taskOrHabit"])

    def log_work(self, minutes: int, end: Optional[datetime] = None) -> None:
        params = {"minutes": minutes}
        if end:
            # Convert local time to Zulu time
            end = end.astimezone(timezone.utc)
            # Truncate timestamp to match required format
            params["end"] = end.isoformat()[:-9] + "Z"

        response = self._client.post(
            f"/api/planner/log-work/task/{self.id}", params=params
        )
        self.from_api_data(response["taskOrHabit"])

    def start(self) -> None:
        response = self._client.post(f"/api/planner/start/task/{self.id}")
        self.from_api_data(response["taskOrHabit"])

    def stop(self) -> None:
        response = self._client.post(f"/api/planner/stop/task/{self.id}")
        self.from_api_data(response["taskOrHabit"])

    def reindex(self, sort_key: float) -> None:
        response = self._client.patch(
            f"{self.ENDPOINT}/{self.id}/reindex",
            json={"sortKey": sort_key},
        )
        self.__dict__.update(self.from_api_data(response).__dict__)


class TaskPatch(BaseModel):
    task_id: int = Field(..., alias="taskId")
    patch: dict[str, Any] = Field(default_factory=dict)
    notification_key: Optional[str] = Field(None, alias="notificationKey")

    model_config = {"populate_by_name": True}
