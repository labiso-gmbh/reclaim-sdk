import httpx
from reclaim_sdk.resources.task import Task


def test_prioritize_by_due_does_not_raise_attribute_error(client, mock_api):
    mock_api.patch("/api/tasks/reindex-by-due").mock(
        return_value=httpx.Response(200, json=[])
    )
    # Must not raise AttributeError — the old code did cls._client which is unset
    Task.prioritize_by_due()
