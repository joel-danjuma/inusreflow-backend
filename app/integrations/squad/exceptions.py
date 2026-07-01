from typing import Any


class SquadAPIError(Exception):
    """Raised for any non-success Squad response -- never silently swallowed.
    Carries the status code and raw body so callers (and audit logs) keep
    the full failure context instead of just a message string.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        raw_response: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.raw_response = raw_response
