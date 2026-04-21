import httpx
from reclaim_sdk.resources.changelog import Changelog, ChangeLogEntryView


def test_changelog_tasks(client, mock_api):
    route = mock_api.get("/api/changelog/tasks").mock(
        return_value=httpx.Response(200, json=[
            {"id": "e1", "entityId": "1", "changeType": "CREATED"},
        ])
    )
    entries = Changelog.tasks([1, 2, 3])
    params = dict(route.calls.last.request.url.params)
    assert "taskIds" in params or any("taskIds" in k for k in params)
    assert len(entries) == 1
    assert isinstance(entries[0], ChangeLogEntryView)


def test_changelog_all(client, mock_api):
    mock_api.get("/api/changelog").mock(return_value=httpx.Response(200, json=[]))
    assert Changelog.all() == []
