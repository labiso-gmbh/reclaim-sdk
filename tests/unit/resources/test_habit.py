import httpx
from reclaim_sdk.resources.habit import DailyHabit


def test_habit_list_hits_assist_endpoint(client, mock_api):
    route = mock_api.get("/api/assist/habits/daily").mock(
        return_value=httpx.Response(200, json=[])
    )
    DailyHabit.list()
    assert route.called


def test_habit_save_creates_new(client, mock_api):
    route = mock_api.post("/api/assist/habits/daily").mock(
        return_value=httpx.Response(200, json={"id": 10, "title": "Run", "type": "CUSTOM_DAILY"})
    )
    h = DailyHabit(title="Run")
    h.save()
    assert h.id == 10


def test_habit_get_by_id(client, mock_api):
    mock_api.get("/api/assist/habits/daily/10").mock(
        return_value=httpx.Response(200, json={"id": 10, "title": "Run", "type": "CUSTOM_DAILY"})
    )
    h = DailyHabit.get(10)
    assert h.title == "Run"


def test_habit_start_uses_habit_segment(client, mock_api):
    route = mock_api.post("/api/planner/start/habit/10").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 10, "type": "CUSTOM_DAILY"}})
    )
    h = DailyHabit(id=10, title="Run")
    h.start()
    assert route.called


def test_habit_restart_uses_habit_segment(client, mock_api):
    route = mock_api.post("/api/planner/restart/habit/10").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 10, "type": "CUSTOM_DAILY"}})
    )
    h = DailyHabit(id=10, title="Run")
    h.restart()
    assert route.called


def test_habit_clear_exceptions(client, mock_api):
    route = mock_api.post("/api/planner/clear-exceptions/habit/10").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 10, "type": "CUSTOM_DAILY"}})
    )
    h = DailyHabit(id=10, title="Run")
    h.clear_exceptions()
    assert route.called


def test_habit_toggle_sends_enable(client, mock_api):
    route = mock_api.post("/api/planner/toggle/habit/10").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 10, "type": "CUSTOM_DAILY"}})
    )
    h = DailyHabit(id=10, title="Run")
    h.toggle(enable=False)
    params = dict(route.calls.last.request.url.params)
    assert params["enable"] == "false"


def test_habit_reschedule_event(client, mock_api):
    route = mock_api.post("/api/planner/reschedule/habit/event/evt-x").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 10, "type": "CUSTOM_DAILY"}})
    )
    DailyHabit(id=10, title="Run").reschedule_event("evt-x")
    assert route.called


def test_habit_skip_event(client, mock_api):
    route = mock_api.post("/api/planner/skip/habit/event/evt-y").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 10, "type": "CUSTOM_DAILY"}})
    )
    DailyHabit(id=10, title="Run").skip_event("evt-y")
    assert route.called


def test_habit_migrate_to_smart_series(client, mock_api):
    route = mock_api.post("/api/assist/habits/daily/10/migrate-to-smart-series").mock(
        return_value=httpx.Response(200, json={})
    )
    DailyHabit(id=10, title="Run").migrate_to_smart_series()
    assert route.called


def test_habit_delete_policy(client, mock_api):
    route = mock_api.delete("/api/planner/policy/habit/10").mock(
        return_value=httpx.Response(200, json={"taskOrHabit": {"id": 10, "type": "CUSTOM_DAILY"}})
    )
    DailyHabit(id=10, title="Run").delete_policy()
    assert route.called
