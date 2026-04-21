from pydantic import BaseModel, Field
import os
import json
from datetime import datetime, timezone
import httpx
from typing import Any, Dict, Optional
from reclaim_sdk.exceptions import (
    ReclaimAPIError,
    RecordNotFound,
    InvalidRecord,
    AuthenticationError,
)


class ReclaimClientConfig(BaseModel):
    token: str = Field(..., description="Reclaim API token")
    base_url: str = Field(
        "https://api.app.reclaim.ai", description="Reclaim API base URL"
    )


class ReclaimClient:
    _instance: Optional["ReclaimClient"] = None
    _config: Optional[ReclaimClientConfig] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        if self._config is None:
            token = os.environ.get("RECLAIM_TOKEN")
            if not token:
                raise ValueError(
                    "Reclaim token is required. Use ReclaimClient.configure() or set RECLAIM_TOKEN environment variable."
                )
            self._config = ReclaimClientConfig(token=token)

        self.session = httpx.Client(
            base_url=self._config.base_url,
            headers={"Authorization": f"Bearer {self._config.token}"},
        )
        self._user_cache: dict | None = None

    @classmethod
    def configure(cls, token: str, base_url: Optional[str] = None) -> "ReclaimClient":
        """Configure the ReclaimClient with the given token and optional base URL."""
        config = ReclaimClientConfig(token=token)
        cls._config = config
        if not cls._instance:
            cls._instance = super().__new__(cls)
        if cls._instance is not None:
            cls._instance._user_cache = None
        cls._instance._initialize()
        return cls._instance

    def request(self, method: str, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        if "json" in kwargs:
            kwargs["content"] = json.dumps(
                kwargs.pop("json"), default=self._datetime_encoder
            )
            kwargs["headers"] = kwargs.get("headers", {})
            kwargs["headers"]["Content-Type"] = "application/json"

        try:
            response = self.session.request(method, endpoint, **kwargs)
            response.raise_for_status()
            if (
                method.upper() == "DELETE"
                and response.status_code in (204, 200)
                and not response.content
            ):
                return {}
            return response.json()
        except httpx.HTTPStatusError as e:
            error_data = (
                e.response.json() if e.response.content else {"message": str(e)}
            )
            if e.response.status_code == 401:
                raise AuthenticationError(
                    f"Authentication failed: {error_data.get('message')}"
                )
            elif e.response.status_code == 404:
                raise RecordNotFound(f"Resource not found: {endpoint}")
            elif e.response.status_code in (400, 422):
                raise InvalidRecord(f"Invalid data: {error_data.get('message')}")
            else:
                raise ReclaimAPIError(f"API error: {error_data.get('message')}")
        except httpx.RequestError as e:
            raise ReclaimAPIError(f"Request failed: {str(e)}")
        except json.JSONDecodeError:
            raise ReclaimAPIError("Invalid JSON response from API")

    @staticmethod
    def _datetime_encoder(obj: Any) -> str:
        if isinstance(obj, datetime):
            return obj.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        raise TypeError(
            f"Object of type {obj.__class__.__name__} is not JSON serializable"
        )

    def get(self, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        return self.request("GET", endpoint, **kwargs)

    def post(self, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        return self.request("POST", endpoint, **kwargs)

    def put(self, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        return self.request("PUT", endpoint, **kwargs)

    def delete(self, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        return self.request("DELETE", endpoint, **kwargs)

    def patch(self, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        return self.request("PATCH", endpoint, **kwargs)

    def current_user(self) -> Dict[str, Any]:
        if self._user_cache is None:
            self._user_cache = self.get("/api/users/current")
        return self._user_cache
