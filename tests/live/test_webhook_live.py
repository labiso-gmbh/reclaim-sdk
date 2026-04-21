import pytest
from reclaim_sdk.resources.webhook import Webhook

pytestmark = pytest.mark.live


def test_webhook_list_works(live_client):
    """Webhook list read path. Create path observed to return server-side 500
    Internal Error on account tiers without webhook feature activated — SDK
    payload is syntactically valid (confirmed: 500 with apiVersion=v2026-04-13,
    status=ACTIVE, valid URL), but the feature itself needs enabling server-side.
    Testing create lifecycle requires an account with webhooks provisioned.
    """
    result = Webhook.list()
    assert isinstance(result, list)
