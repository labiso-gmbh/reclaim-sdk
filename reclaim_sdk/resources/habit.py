from typing import ClassVar, Optional
from pydantic import Field
from reclaim_sdk.resources.base import BaseResource
from reclaim_sdk.enums import EventCategory, EventColor, PriorityLevel


class DailyHabit(BaseResource):
    ENDPOINT: ClassVar[str] = "/api/assist/habits/daily"
    _PLANNER_PATH_SEGMENT: ClassVar[str] = "habit"

    title: Optional[str] = Field(None, description="Habit title")
    description: Optional[str] = Field(None, description="Habit description")
    priority: Optional[PriorityLevel] = Field(None)
    event_category: EventCategory = Field(
        default=EventCategory.PERSONAL, alias="eventCategory"
    )
    event_color: Optional[EventColor] = Field(None, alias="eventColor")
    always_private: bool = Field(False, alias="alwaysPrivate")
    enabled: bool = Field(True)
    type: str = Field("CUSTOM_DAILY", description="Discriminator")
