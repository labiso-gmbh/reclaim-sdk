from datetime import datetime
from typing import Any, ClassVar, Optional
from pydantic import Field
from reclaim_sdk.resources.base import BaseResource
from reclaim_sdk.enums import EventCategory, EventColor, EventSubType, PriorityLevel


class DailyHabit(BaseResource):
    ENDPOINT: ClassVar[str] = "/api/assist/habits/daily"
    _PLANNER_PATH_SEGMENT: ClassVar[str] = "habit"

    title: Optional[str] = Field(None, description="Habit title")
    description: Optional[str] = Field(None, description="Habit description")
    priority: Optional[PriorityLevel] = Field(None)
    event_category: EventCategory = Field(
        default=EventCategory.PERSONAL, alias="eventCategory"
    )
    event_sub_type: Optional[EventSubType] = Field(None, alias="eventSubType")
    event_color: Optional[EventColor] = Field(None, alias="eventColor")
    always_private: bool = Field(False, alias="alwaysPrivate")
    enabled: bool = Field(True)
    type: str = Field("CUSTOM_DAILY", description="Discriminator")

    # Additional fields from Swagger DailyHabit schema
    created: Optional[datetime] = Field(None, description="Creation timestamp")
    updated: Optional[datetime] = Field(None, description="Last update timestamp")
    snooze_until: Optional[datetime] = Field(None, alias="snoozeUntil")
    defense_aggression: Optional[str] = Field(None, alias="defenseAggression")
    defended_description: Optional[str] = Field(None, alias="defendedDescription")
    recurring_assignment_type: Optional[str] = Field(
        None, alias="recurringAssignmentType"
    )
    invitees: Optional[list[dict[str, Any]]] = Field(None)
    duration_min: Optional[int] = Field(None, alias="durationMin")
    duration_max: Optional[int] = Field(None, alias="durationMax")
    ideal_time: Optional[str] = Field(None, alias="idealTime")
    ideal_day: Optional[str] = Field(None, alias="idealDay")
    recurrence: Optional[dict[str, Any]] = Field(None)
    times_per_period: Optional[int] = Field(None, alias="timesPerPeriod")
    additional_description: Optional[str] = Field(None, alias="additionalDescription")
    index: Optional[int] = Field(None)
    elevated: Optional[bool] = Field(None)
    reserved_words: Optional[list[str]] = Field(None, alias="reservedWords")
    notification: Optional[bool] = Field(None)
    time_policy_type: Optional[str] = Field(None, alias="timePolicyType")
    one_off_policy: Optional[dict[str, Any]] = Field(None, alias="oneOffPolicy")
    time_scheme_id: Optional[str] = Field(None, alias="timeSchemeId")
    auto_decline: Optional[bool] = Field(None, alias="autoDecline")
    auto_decline_text: Optional[str] = Field(None, alias="autoDeclineText")
    adjusted: Optional[bool] = Field(None)
    prioritizable_type: Optional[str] = Field(None, alias="prioritizableType")
