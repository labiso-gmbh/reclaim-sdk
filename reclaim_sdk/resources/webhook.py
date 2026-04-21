from datetime import datetime
from typing import ClassVar, Optional
from pydantic import Field
from reclaim_sdk.resources.base import BaseResource


class Webhook(BaseResource):
    ENDPOINT: ClassVar[str] = "/api/team/current/webhooks"

    url: Optional[str] = Field(None, description="Receiver URL")
    events: list[str] = Field(
        default_factory=list, description="Subscribed event types"
    )
    secret: Optional[str] = Field(
        None, description="HMAC signing secret (if server supports)"
    )

    # Additional fields from Swagger WebhookConfig / WebhookConfigRequest schemas
    name: Optional[str] = Field(None, description="Webhook display name (3-40 chars)")
    status: Optional[str] = Field(
        None, description="Webhook status (ACTIVE/SUSPENDED/DISABLED/DOWNGRADED)"
    )
    api_version: Optional[str] = Field(
        None, alias="apiVersion", description="Webhook API version"
    )
    created_at: Optional[datetime] = Field(
        None, alias="createdAt", description="Webhook creation timestamp"
    )

    model_config = {"populate_by_name": True}
