import pytest
from reclaim_sdk.resources.hours import Hours

pytestmark = pytest.mark.live


def test_hours_list_returns_schemes(live_client):
    schemes = Hours.list()
    assert isinstance(schemes, list)
