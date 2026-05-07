from reclaim_sdk.enums import (
    PriorityLevel, EventCategory, EventColor, TaskStatus,
    TaskSource, SnoozeOption, EventSubType,
    Weekday, TimeSchemeFeature, PolicyType,
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


def test_weekday_has_seven_days():
    values = {e.value for e in Weekday}
    assert values == {"MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY",
                      "FRIDAY", "SATURDAY", "SUNDAY"}


def test_time_scheme_feature_known_values():
    values = {e.value for e in TimeSchemeFeature}
    expected = {
        "TASK_ASSIGNMENT", "HABIT_ASSIGNMENT", "SCHEDULING_LINK_MEETING",
        "SMART_HABIT", "ONE_ON_ONE_ASSIGNMENT", "SMART_MEETING",
    }
    # must cover the six features observed live; allow forward-compatible extras
    assert expected.issubset(values)


def test_policy_type_covers_observed_values():
    values = {e.value for e in PolicyType}
    assert {"CUSTOM", "WORK", "PERSONAL", "MEETING"}.issubset(values)
