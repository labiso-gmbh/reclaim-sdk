import httpx
from reclaim_sdk.resources.hours import Hours


def test_hours_list(client, mock_api):
    route = mock_api.get("/api/timeschemes").mock(
        return_value=httpx.Response(200, json=[{
            "id": "ts-1", "status": "ACTIVE", "title": "Work",
            "description": "Work hours", "features": [],
        }])
    )
    result = Hours.list()
    assert len(result) == 1
    assert result[0].id == "ts-1"
