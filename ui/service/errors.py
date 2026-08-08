"""Typed HTTP error envelope + search error mapping (GUI_ROADMAP.md § 7).

Task-004 scope: the `{"error": {"code", "message", "details"}}` envelope and the
`GRAPH_NOT_FOUND` -> 503 mapping.

Task-012 scope: `INVALID_INPUT`, `ALGORITHM_UNKNOWN`, `ALGORITHM_UNAVAILABLE`,
`SEARCH_FAILED`, `SEARCH_TIMEOUT` and the `status_code` / `ErrorEnvelope` helpers
used by `main.create_search`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fastapi.responses import JSONResponse

__all__ = [
    "AlgorithmUnavailableError",
    "AlgorithmUnknownError",
    "ErrorEnvelope",
    "InvalidInputError",
    "SearchError",
    "SearchFailedError",
    "SearchTimeoutError",
    "error_response",
    "graph_not_found",
    "internal_error",
    "to_envelope",
]


@dataclass(frozen=True)
class ErrorEnvelope:
    """A typed § 7 error envelope; JSON-serializable via `to_dict`."""

    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return the JSON-safe § 7 error envelope dict."""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": dict(self.details),
            }
        }


def to_envelope(
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the § 7 error envelope for a failing request."""
    return ErrorEnvelope(code=code, message=message, details=details or {}).to_dict()


def error_response(
    status_code: int,
    envelope: ErrorEnvelope,
) -> JSONResponse:
    """Return an HTTP response carrying a typed § 7 error envelope."""
    return JSONResponse(status_code=status_code, content=envelope.to_dict())


def graph_not_found() -> JSONResponse:
    """Return the `503 GRAPH_NOT_FOUND` § 7 error response body."""
    return error_response(
        status_code=503,
        envelope=ErrorEnvelope(
            code="GRAPH_NOT_FOUND",
            message="Graph files are missing or failed to load.",
        ),
    )


def internal_error(
    message: str = "Internal server error.",
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    """Return the `500 INTERNAL` § 7 error response body for unknown failures."""
    return error_response(
        status_code=500,
        envelope=ErrorEnvelope(code="INTERNAL", message=message, details=details or {}),
    )


class SearchError(Exception):
    """Base for search failures that map to a § 7 HTTP error."""

    code = "SEARCH_ERROR"
    status_code = 500

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def to_envelope(self) -> ErrorEnvelope:
        return ErrorEnvelope(code=self.code, message=self.message)


class InvalidInputError(SearchError):
    """A request field failed validation; `400 INVALID_INPUT`."""

    code = "INVALID_INPUT"
    status_code = 400


class AlgorithmUnknownError(SearchError):
    """The requested algorithm name is not registered; `404 ALGORITHM_UNKNOWN`."""

    code = "ALGORITHM_UNKNOWN"
    status_code = 404


class AlgorithmUnavailableError(SearchError):
    """The algorithm exists but cannot run here; `409 ALGORITHM_UNAVAILABLE`."""

    code = "ALGORITHM_UNAVAILABLE"
    status_code = 409


class SearchFailedError(SearchError):
    """The search failed while running; `500 SEARCH_FAILED`."""

    code = "SEARCH_FAILED"
    status_code = 500


class SearchTimeoutError(SearchError):
    """The search exceeded the configured timeout; `504 SEARCH_TIMEOUT`."""

    code = "SEARCH_TIMEOUT"
    status_code = 504