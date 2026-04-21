from typing import ClassVar
import httpx
from pydantic import Field
from reclaim_sdk.resources.base import BaseResource


class _Sample(BaseResource):
    ENDPOINT: ClassVar[str] = "/api/sample"
    USER_PARAM_REQUIRED: ClassVar[bool] = True
    title: str | None = Field(None)


def test_list_injects_user_when_required(client, mock_api):
    mock_api.get("/api/users/current").mock(
        return_value=httpx.Response(200, json={"id": 7})
    )
    route = mock_api.get("/api/sample").mock(
        return_value=httpx.Response(200, json=[])
    )
    _Sample.list()
    assert route.called
    assert "user" in dict(route.calls.last.request.url.params)


def test_get_injects_user_when_required(client, mock_api):
    mock_api.get("/api/users/current").mock(
        return_value=httpx.Response(200, json={"id": 7})
    )
    route = mock_api.get("/api/sample/1").mock(
        return_value=httpx.Response(200, json={"id": 1, "title": "x"})
    )
    _Sample.get(1)
    assert "user" in dict(route.calls.last.request.url.params)


def test_no_user_injection_when_not_required(client, mock_api):
    class _NoUser(BaseResource):
        ENDPOINT: ClassVar[str] = "/api/nouser"
        title: str | None = Field(None)

    route = mock_api.get("/api/nouser").mock(return_value=httpx.Response(200, json=[]))
    _NoUser.list()
    assert "user" not in dict(route.calls.last.request.url.params)


def test_save_with_put_strategy_uses_put(client, mock_api):
    mock_api.get("/api/users/current").mock(return_value=httpx.Response(200, json={"id": 1}))
    route = mock_api.put("/api/sample/5").mock(
        return_value=httpx.Response(200, json={"id": 5, "title": "x"})
    )
    s = _Sample(id=5, title="x")
    s.save(strategy="put")
    assert route.called
