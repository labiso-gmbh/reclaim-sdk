"""Webhook subscription + consumption example.

Subscribing requires the `apiVersion` field (enum, e.g. "v2026-04-13") and a
valid `status` (e.g. "ACTIVE"). The webhook feature may need to be provisioned
on your account by Reclaim before POST succeeds — contact support if you see
500 Internal Error responses on create.

Event type literals (`task.created`, `habit.updated`, …) are inferred from the
SDK's typed payload models. If a specific literal is rejected by the server,
omit it from the subscription and use the discriminated union on receive.
"""

from reclaim_sdk.resources.webhook import Webhook
from reclaim_sdk.webhooks import (
    parse_webhook_payload,
    verify_signature,
    TaskWebhookEvent,
    HabitWebhookEvent,
)

# List existing subscriptions
for wh in Webhook.list():
    print(f"{wh.id}: {wh.url} (status={wh.status}, events={wh.events})")

# Create a subscription
wh = Webhook(
    url="https://yourapp.example.com/reclaim-hook",
    events=["task.created", "task.updated", "task.completed"],
    status="ACTIVE",
    api_version="v2026-04-13",
    name="my-integration",
)
# wh.save()  # uncomment once webhooks are provisioned on your account

# In your receiver (Flask-ish pseudocode):
#
# def hook(request):
#     verify_signature(
#         request.data,
#         request.headers["X-Reclaim-Signature"],
#         MY_WEBHOOK_SECRET,
#     )
#     event = parse_webhook_payload(request.data)
#     if isinstance(event, TaskWebhookEvent):
#         print(event.task.id, event.task.title)
#     elif isinstance(event, HabitWebhookEvent):
#         print(event.habit.id, event.habit.title)
