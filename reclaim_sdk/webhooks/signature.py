"""Webhook signature verification.

Reclaim signature header name and algorithm are verified during live-mode
discovery (register a test webhook, inspect headers). Current implementation
assumes HMAC-SHA256 hex digest of the raw request body with the subscriber's
secret. If live observation shows Reclaim uses a different scheme, update the
`verify_signature` function accordingly — or replace the body with
`raise NotImplementedError(...)` if no signature is actually emitted.
"""

import hmac
import hashlib
from reclaim_sdk.exceptions import SignatureVerificationError


def verify_signature(body: bytes, header: str, secret: str) -> bool:
    if not header:
        raise SignatureVerificationError("empty signature header")
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, header):
        raise SignatureVerificationError("signature mismatch")
    return True
