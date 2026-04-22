import httpx
import pytest
from reclaim_sdk.client import ReclaimClient


def test_current_user_fetches_and_caches(client, mock_api):
    route = mock_api.get("/api/users/current").mock(
        return_value=httpx.Response(200, json={"id": 42, "username": "alice"})
    )
    user_a = client.current_user()
    user_b = client.current_user()
    assert user_a == user_b
    assert user_a["id"] == 42
    assert route.call_count == 1  # cache works


def test_current_user_cache_cleared_on_reconfigure(client, mock_api):
    mock_api.get("/api/users/current").mock(
        return_value=httpx.Response(200, json={"id": 1})
    )
    client.current_user()
    ReclaimClient.configure(token="another-token")
    # After reconfigure, cache must be invalidated
    assert ReclaimClient._instance._user_cache is None


def test_configure_without_token_raises_when_env_missing(monkeypatch):
    monkeypatch.delenv("RECLAIM_TOKEN", raising=False)
    ReclaimClient._instance = None
    ReclaimClient._config = None
    with pytest.raises(ValueError, match="token is required"):
        ReclaimClient()


def test_configure_honours_base_url():
    """Regression: configure(token, base_url=...) must store the base_url, not silently drop it."""
    client = ReclaimClient.configure(token="t", base_url="https://staging.reclaim.ai")
    assert ReclaimClient._config.base_url == "https://staging.reclaim.ai"
    # The httpx session must also be wired to the override host.
    assert str(client.session.base_url).rstrip("/") == "https://staging.reclaim.ai"


def test_configure_default_base_url_when_omitted():
    """Default base_url is preserved when caller passes only the token."""
    ReclaimClient.configure(token="t")
    assert ReclaimClient._config.base_url == "https://api.app.reclaim.ai"
