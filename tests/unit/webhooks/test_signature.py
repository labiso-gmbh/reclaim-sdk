import hmac
import hashlib
import pytest
from reclaim_sdk.webhooks.signature import verify_signature, SignatureVerificationError


SECRET = "s3cret"


def _sign(body: bytes) -> str:
    return hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()


def test_valid_signature_returns_true():
    body = b'{"x":1}'
    assert verify_signature(body, _sign(body), SECRET) is True


def test_invalid_signature_raises():
    with pytest.raises(SignatureVerificationError):
        verify_signature(b'{"x":1}', "deadbeef", SECRET)


def test_empty_signature_raises():
    with pytest.raises(SignatureVerificationError):
        verify_signature(b'{}', "", SECRET)
