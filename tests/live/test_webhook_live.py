import pytest
from reclaim_sdk.resources.webhook import Webhook

pytestmark = pytest.mark.live


def test_webhook_create_list_delete(live_client, tracked_ids):
    w = Webhook(url="https://example.test/hook", events=["task.created"])
    w.save()
    tracked_ids["webhooks"].append(w.id)
    assert w.id is not None
    assert w.id in [x.id for x in Webhook.list()]
