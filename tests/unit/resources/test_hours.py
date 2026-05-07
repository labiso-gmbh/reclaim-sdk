import json
from datetime import time

import httpx

from reclaim_sdk.enums import PolicyType, TimeSchemeFeature, Weekday
from reclaim_sdk.resources.hours import (
    Hours, Interval, DayIntervals, TimeSchemePolicy,
)


# Single live response captured from app.reclaim.ai.har — the canonical
# server shape for a built-in scheme.
SAMPLE_SERVER_SCHEME = {
    "id": "9ad7db76-8ce9-4d1f-a25f-6f082f05fa83",
    "userId": "d589ace5-0d37-4ac2-a203-1aa095886e28",
    "status": "ACTIVE",
    "policyType": "MEETING",
    "policy": {
        "dayHours": {
            "TUESDAY": {
                "intervals": [{"start": "09:00:00", "end": "17:00:00", "duration": 28800.0}],
                "startOfDay": "09:00:00",
                "endOfDay": "17:00:00",
            },
            "WEDNESDAY": {
                "intervals": [{"start": "09:00:00", "end": "17:00:00", "duration": 28800.0}],
                "startOfDay": "09:00:00",
                "endOfDay": "17:00:00",
            },
        },
        "startOfWeek": "TUESDAY",
        "endOfWeek": "WEDNESDAY",
    },
    "title": "Meeting Hours",
    "description": "For meetings",
    "features": ["HABIT_ASSIGNMENT", "ONE_ON_ONE_ASSIGNMENT"],
    "taskTargetCalendar": {"id": 1007449, "name": "primary"},
    "taskTargetCalendarId": None,
}


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def test_hours_parses_server_scheme(client):
    h = Hours.from_api_data(SAMPLE_SERVER_SCHEME)
    assert h.id == "9ad7db76-8ce9-4d1f-a25f-6f082f05fa83"
    assert h.policy_type == PolicyType.MEETING
    assert Weekday.TUESDAY in h.policy.day_hours
    assert h.policy.day_hours[Weekday.TUESDAY].intervals[0].start == time(9, 0)
    assert h.policy.start_of_week == Weekday.TUESDAY


def test_hours_features_decode_to_enum(client):
    h = Hours.from_api_data(SAMPLE_SERVER_SCHEME)
    assert TimeSchemeFeature.HABIT_ASSIGNMENT in h.features
    assert TimeSchemeFeature.ONE_ON_ONE_ASSIGNMENT in h.features


def test_hours_keeps_task_target_calendar_object(client):
    h = Hours.from_api_data(SAMPLE_SERVER_SCHEME)
    assert h.task_target_calendar == {"id": 1007449, "name": "primary"}


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

def test_hours_to_api_data_uses_camel_case_aliases(client):
    """``to_api_data`` returns a Python dict shaped for the wire — alias keys
    are camelCase. (Datetime/time objects are stringified later by the
    client's JSON encoder; ``test_hours_save_post_sends_har_shaped_body``
    asserts the on-wire bytes.)"""
    h = Hours(
        title="Test Hours",
        description="t",
        task_category="WORK",
        policy_type=PolicyType.CUSTOM,
        policy=TimeSchemePolicy(day_hours={
            Weekday.MONDAY: DayIntervals(intervals=[
                Interval(start=time(9, 0), end=time(17, 0)),
            ]),
        }),
        features=[TimeSchemeFeature.TASK_ASSIGNMENT],
        task_target_calendar_id=1007449,
    )
    payload = h.to_api_data()
    assert payload["taskCategory"] == "WORK"
    assert payload["policyType"] == "CUSTOM"
    assert payload["taskTargetCalendarId"] == 1007449
    assert payload["features"] == [TimeSchemeFeature.TASK_ASSIGNMENT]
    interval = payload["policy"]["dayHours"][Weekday.MONDAY]["intervals"][0]
    assert interval["start"] == time(9, 0)
    assert interval["end"] == time(17, 0)


def test_hours_to_api_data_omits_none_calendar_object(client):
    """``task_target_calendar`` is server-resolved; SDK should not echo a
    None back as ``"taskTargetCalendar": null``."""
    h = Hours(title="x", description="y", features=[])
    payload = h.to_api_data()
    assert "taskTargetCalendar" not in payload


# ---------------------------------------------------------------------------
# CRUD against the wire
# ---------------------------------------------------------------------------

def test_hours_list_parses_full_scheme(client, mock_api):
    mock_api.get("/api/timeschemes").mock(
        return_value=httpx.Response(200, json=[SAMPLE_SERVER_SCHEME])
    )
    schemes = Hours.list()
    assert len(schemes) == 1
    assert schemes[0].policy_type == PolicyType.MEETING


def test_hours_get_returns_single_scheme(client, mock_api):
    mock_api.get(f"/api/timeschemes/{SAMPLE_SERVER_SCHEME['id']}").mock(
        return_value=httpx.Response(200, json=SAMPLE_SERVER_SCHEME)
    )
    h = Hours.get(SAMPLE_SERVER_SCHEME["id"])
    assert h.title == "Meeting Hours"


def test_hours_save_post_sends_har_shaped_body(client, mock_api):
    """Body must match the captured POST /api/timeschemes HAR shape:
    title, description, taskCategory, policyType=CUSTOM, policy.dayHours,
    features, taskTargetCalendarId."""
    captured = {}

    def respond(request):
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={**SAMPLE_SERVER_SCHEME, "title": "Test Hours"})

    mock_api.post("/api/timeschemes").mock(side_effect=respond)

    h = Hours(
        title="Test Hours",
        description="Test Description",
        task_category="WORK",
        policy_type=PolicyType.CUSTOM,
        policy=TimeSchemePolicy(day_hours={
            Weekday.MONDAY: DayIntervals(intervals=[
                Interval(start=time(9, 0), end=time(17, 0)),
            ]),
        }),
        features=[
            TimeSchemeFeature.TASK_ASSIGNMENT,
            TimeSchemeFeature.SCHEDULING_LINK_MEETING,
        ],
        task_target_calendar_id=1007449,
    )
    h.save()

    body = captured["body"]
    assert body["title"] == "Test Hours"
    assert body["taskCategory"] == "WORK"
    assert body["policyType"] == "CUSTOM"
    assert body["policy"]["dayHours"]["MONDAY"]["intervals"] == [
        {"start": "09:00:00", "end": "17:00:00"}
    ]
    assert body["taskTargetCalendarId"] == 1007449
    assert "TASK_ASSIGNMENT" in body["features"]


def test_hours_save_with_id_patches(client, mock_api):
    scheme_id = SAMPLE_SERVER_SCHEME["id"]
    route = mock_api.patch(f"/api/timeschemes/{scheme_id}").mock(
        return_value=httpx.Response(200, json=SAMPLE_SERVER_SCHEME)
    )
    h = Hours.from_api_data(SAMPLE_SERVER_SCHEME)
    h.title = "Renamed"
    h.save()
    assert route.called


def test_hours_delete(client, mock_api):
    scheme_id = SAMPLE_SERVER_SCHEME["id"]
    route = mock_api.delete(f"/api/timeschemes/{scheme_id}").mock(
        return_value=httpx.Response(204)
    )
    h = Hours.from_api_data(SAMPLE_SERVER_SCHEME)
    h.delete()
    assert route.called


# ---------------------------------------------------------------------------
# Backward compatibility — existing test from before the rewrite
# ---------------------------------------------------------------------------

def test_hours_list_minimal_legacy_shape(client, mock_api):
    """Pre-rewrite Hours objects only had id/status/title/description/features.
    The rewritten model must still parse that minimal shape."""
    mock_api.get("/api/timeschemes").mock(
        return_value=httpx.Response(200, json=[{
            "id": "ts-1",
            "status": "ACTIVE",
            "title": "Work",
            "description": "Work hours",
            "features": [],
        }])
    )
    result = Hours.list()
    assert len(result) == 1
    assert result[0].id == "ts-1"
    assert result[0].policy is None
