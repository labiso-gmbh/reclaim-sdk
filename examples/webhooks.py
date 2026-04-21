from reclaim_sdk.resources.webhook import Webhook
from reclaim_sdk.webhooks import parse_webhook_payload, verify_signature, TaskWebhookEvent

# Subscribe
wh = Webhook(url="https://yourapp.test/reclaim-hook",
             events=["task.created", "task.updated", "task.completed"])
wh.save()

# In your receiver (Flask example):
# def hook(request):
#     verify_signature(request.data, request.headers["X-Reclaim-Signature"], SECRET)
#     event = parse_webhook_payload(request.data)
#     if isinstance(event, TaskWebhookEvent):
#         print(event.task.title)
