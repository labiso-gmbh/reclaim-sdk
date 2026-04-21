class ReclaimAPIError(Exception):
    """Base exception for Reclaim API errors"""


class RecordNotFound(ReclaimAPIError):
    """Raised when a requested resource is not found"""


class InvalidRecord(ReclaimAPIError):
    """Raised when invalid data is submitted to the API"""


class AuthenticationError(ReclaimAPIError):
    """Raised when there's an authentication problem"""


class SignatureVerificationError(ReclaimAPIError):
    """Raised when a webhook signature does not match."""
