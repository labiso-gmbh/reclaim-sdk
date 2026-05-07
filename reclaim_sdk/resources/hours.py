"""Reclaim *time scheme* (a.k.a. **Hours**) resource.

Backs ``/api/timeschemes`` — a customer's working-hours profile. Each scheme
declares **when** Reclaim is allowed to schedule what (work tasks vs. meetings
vs. personal habits) by listing time intervals per weekday.

Supports full CRUD (POST / GET / PATCH / DELETE) via :class:`BaseResource`.
"""

from datetime import time
from typing import ClassVar, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from reclaim_sdk.enums import PolicyType, TimeSchemeFeature, Weekday
from reclaim_sdk.resources.base import BaseResource


class _CamelModel(BaseModel):
    """Shared config: camelCase aliases, allow forward-compatible extra keys."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",
    )


class Interval(_CamelModel):
    """Single ``[start, end)`` working-time slot inside a day."""

    start: time = Field(..., description="Slot start (HH:MM:SS, local-day time)")
    end: time = Field(..., description="Slot end (HH:MM:SS, local-day time)")
    duration: Optional[float] = Field(
        None, description="Length in seconds (server-computed, ignored on write)"
    )


class DayIntervals(_CamelModel):
    """Working intervals for one weekday, plus optional convenience bounds."""

    intervals: List[Interval] = Field(default_factory=list)
    start_of_day: Optional[time] = Field(None, alias="startOfDay")
    end_of_day: Optional[time] = Field(None, alias="endOfDay")


class TimeSchemePolicy(_CamelModel):
    """Per-weekday breakdown of allowed working times."""

    day_hours: Dict[Weekday, DayIntervals] = Field(
        default_factory=dict,
        alias="dayHours",
        description="Map of weekday -> intervals; omit a weekday to mark it off",
    )
    start_of_week: Optional[Weekday] = Field(None, alias="startOfWeek")
    end_of_week: Optional[Weekday] = Field(None, alias="endOfWeek")


class Hours(BaseResource):
    """A Reclaim *time scheme* — full CRUD against ``/api/timeschemes``."""

    model_config = ConfigDict(
        alias_generator=None,
        populate_by_name=True,
        extra="allow",
    )

    ENDPOINT: ClassVar[str] = "/api/timeschemes"

    # Override BaseResource.id (int) — time schemes use UUID strings
    id: Optional[str] = Field(None, description="Time scheme UUID")

    title: Optional[str] = Field(None, description="Display title")
    description: Optional[str] = Field(None, description="Free-text description")
    status: Optional[str] = Field(None, description="Lifecycle status (e.g. ACTIVE)")
    user_id: Optional[str] = Field(None, alias="userId")
    task_category: Optional[str] = Field(
        None,
        alias="taskCategory",
        description="Category default for tasks/habits using this scheme",
    )
    policy_type: Optional[PolicyType] = Field(
        None,
        alias="policyType",
        description="``CUSTOM`` for user-defined hours; preset values bind to "
        "the user's main Work/Personal/Meeting hours",
    )
    policy: Optional[TimeSchemePolicy] = Field(
        None, description="Per-weekday intervals (required when ``policy_type=CUSTOM``)"
    )
    features: List[TimeSchemeFeature] = Field(
        default_factory=list,
        description="Capabilities this scheme provides (which Reclaim flows may use it)",
    )
    task_target_calendar_id: Optional[int] = Field(
        None,
        alias="taskTargetCalendarId",
        description="Calendar ID where events scheduled from this scheme land",
    )
    task_target_calendar: Optional[Dict] = Field(
        None,
        alias="taskTargetCalendar",
        description="Server-resolved calendar object (read-only mirror of "
        "``task_target_calendar_id``)",
    )
