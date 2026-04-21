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
