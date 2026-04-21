import httpx
from reclaim_sdk.resources.webhook import Webhook


def test_webhook_list(client, mock_api):
    mock_api.get("/api/team/current/webhooks").mock(
        return_value=httpx.Response(200, json=[])
    )
    Webhook.list()


def test_webhook_create(client, mock_api):
    mock_api.post("/api/team/current/webhooks").mock(
        return_value=httpx.Response(200, json={"id": 1, "url": "https://x.test", "events": ["task.created"]})
    )
    w = Webhook(url="https://x.test", events=["task.created"])
    w.save()
    assert w.id == 1


def test_webhook_delete(client, mock_api):
    route = mock_api.delete("/api/team/current/webhooks/1").mock(
        return_value=httpx.Response(204)
    )
    w = Webhook(id=1, url="https://x.test", events=["task.created"])
    w.delete()
    assert route.called
