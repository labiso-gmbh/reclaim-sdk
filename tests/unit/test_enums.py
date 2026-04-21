from reclaim_sdk.enums import (
    PriorityLevel, EventCategory, EventColor, TaskStatus,
    TaskSource, SnoozeOption, EventSubType,
)


def test_priority_level_values():
    assert PriorityLevel.P1.value == "P1"
    assert PriorityLevel.P4.value == "P4"
    assert len(list(PriorityLevel)) == 4


def test_event_category_values():
    assert EventCategory.WORK.value == "WORK"
    assert EventCategory.PERSONAL.value == "PERSONAL"


def test_event_color_contains_tomato():
    assert EventColor.TOMATO.value == "TOMATO"


def test_task_status_includes_archived():
    assert TaskStatus.ARCHIVED.value == "ARCHIVED"


def test_task_source_is_string_enum():
    assert isinstance(TaskSource.RECLAIM, TaskSource)
    assert TaskSource.RECLAIM.value == "RECLAIM"


def test_snooze_option_has_options():
    # Must contain at least one known value from Swagger
    values = {e.value for e in SnoozeOption}
    assert "FROM_NOW_1H" in values or "NEXT_WEEK" in values


def test_event_sub_type_is_enum():
    # Just ensure it's importable and has members
    assert len(list(EventSubType)) > 0
