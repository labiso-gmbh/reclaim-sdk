import pytest
from reclaim_sdk.resources.changelog import Changelog

pytestmark = pytest.mark.live


def test_changelog_all(live_client):
    assert isinstance(Changelog.all(), list)
