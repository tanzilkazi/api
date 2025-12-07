class APIBaseError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class APIClientError(Exception):
    """Raised for 4xx client errors (except auth)."""


class APIServerError(Exception):
    """Raised for 5xx server errors."""


class APITimeoutError(Exception):
    """Raised when a request times out after retries."""


class APIAuthError(Exception):
    """Raised for authentication errors (401/403)."""


class APIConnectionError(Exception):
    """Raised for network-level errors (requests exceptions)."""
