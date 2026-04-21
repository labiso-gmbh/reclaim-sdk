import os
import pytest
import respx
from reclaim_sdk.client import ReclaimClient


@pytest.fixture(autouse=True)
def reset_client_singleton():
    """Every test gets a fresh client instance."""
    ReclaimClient._instance = None
    ReclaimClient._config = None
    yield
    ReclaimClient._instance = None
    ReclaimClient._config = None


@pytest.fixture
def client():
    return ReclaimClient.configure(token="test-token")


@pytest.fixture
def mock_api():
    with respx.mock(base_url="https://api.app.reclaim.ai", assert_all_called=False) as mock:
        yield mock


def pytest_collection_modifyitems(config, items):
    if os.environ.get("RECLAIM_LIVE_TEST") == "1":
        return
    skip_live = pytest.mark.skip(reason="set RECLAIM_LIVE_TEST=1 to run")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)
