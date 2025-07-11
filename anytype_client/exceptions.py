"""Custom exceptions for the Anytype client."""
from typing import Any, Dict, Optional
import httpx


class AnytypeError(Exception):
    """Base exception for all Anytype client errors."""

    pass


class APIError(AnytypeError):
    """Base exception for all API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[httpx.Response] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response = response
        self.details = details


class AuthenticationError(APIError):
    """Raised when authentication fails."""

    pass


class BadRequestError(APIError):
    """Raised when the server cannot process the request due to client error."""

    pass


class UnauthorizedError(APIError):
    """Raised when authentication is required but not provided or invalid."""

    pass


class ForbiddenError(APIError):
    """Raised when the request is not allowed for the authenticated user."""

    pass


class NotFoundError(APIError):
    """Raised when a requested resource is not found."""

    pass


class ConflictError(APIError):
    """Raised when there's a conflict with the current state of the resource."""

    pass


class RateLimitError(APIError):
    """Raised when the rate limit is exceeded."""

    def __init__(self, message: str, retry_after: int = 60, *args, **kwargs):
        super().__init__(message, *args, **kwargs)
        self.retry_after = retry_after


class TooManyRequestsError(RateLimitError):
    """Raised when too many requests have been made in a given amount of time."""

    pass


class ServerError(APIError):
    """Raised when the server encounters an error."""

    pass


class TimeoutError(APIError):
    """Raised when a request times out."""

    pass


class ValidationError(APIError):
    """Raised when input validation fails."""

    pass
