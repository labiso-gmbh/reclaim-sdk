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
