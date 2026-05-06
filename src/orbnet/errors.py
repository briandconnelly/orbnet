"""Error translation for the Orb MCP server.

A pure dispatch from raised exceptions (httpx transport errors, HTTP status
errors, Pydantic validation errors) to structured `ErrorPayload` envelopes
agents can branch on.

This module is import-light: it depends only on `models` for the types it
emits, plus `httpx` and `pydantic` for the exception types it dispatches on.
"""

import httpx
from pydantic import BaseModel, ConfigDict, ValidationError

from .models import ErrorPayload, Granularity, Repair

GRANULARITY_FALLBACK: dict[Granularity, Granularity | None] = {
    "1s": "15s",
    "15s": "1m",
    "1m": None,
}
"""Granularity fallback chain. Keyed by the granularity that failed; value
is the next one to try, or `None` if the chain is exhausted (1m is the
most retention-friendly granularity, and if it's unavailable the lower ones
typically aren't enabled either)."""


FAMILY_TO_TOOL_NAME: dict[str, str] = {
    "scores": "get_scores_1m",
    "responsiveness": "get_responsiveness",
    "web_responsiveness": "get_web_responsiveness",
    "speed_results": "get_speed_results",
    "wifi_link": "get_wifi_link",
}
"""Maps `DatasetSpec.family` values to the canonical MCP tool name. Most
families round-trip via `f"get_{family}"`; `scores` is the only entry whose
canonical tool name (`get_scores_1m`) deviates from that pattern, so we keep
the whole mapping as one explicit table."""


class ErrorContext(BaseModel):
    """Per-call context threaded into `translate_exception`.

    Optional throughout the dispatch — translation works without it but
    emits weaker repair info (e.g., a 404 with no `tool`/`granularity` set
    becomes `dataset_not_found` rather than `granularity_unavailable`).
    """

    tool: str | None = None
    granularity: Granularity | None = None

    model_config = ConfigDict(extra="forbid")


def translate_exception(
    exc: BaseException, context: ErrorContext | None = None
) -> ErrorPayload:
    """Translate a raised exception into a structured `ErrorPayload`.

    Pure: no I/O, no logging, no side effects. Dispatch order matches
    `docs/superpowers/specs/2026-05-05-mcp-error-contract-design.md`
    §Translation. First match wins.

    Categorization choices:
    - All `httpx.NetworkError` subclasses route to `sensor_unreachable`. This
      covers `ConnectError`, `ReadError`, `WriteError`, `ProtocolError`,
      `RemoteProtocolError`, etc.
    - `httpx.ConnectTimeout` is a `TimeoutException` subclass (NOT a
      `NetworkError` subclass), so it routes to the `timeout` branch below.
    """
    if isinstance(exc, httpx.NetworkError):
        return ErrorPayload(
            error=str(exc),
            code="sensor_unreachable",
            repair=Repair(
                next_step=(
                    "verify the sensor is on the network and Local API is enabled"
                ),
                alternative="check ORB_HOST and ORB_PORT settings",
            ),
        )

    if isinstance(exc, httpx.TimeoutException):
        return ErrorPayload(
            error=str(exc),
            code="timeout",
            repair=Repair(
                next_step="increase the timeout parameter, or wait and retry"
            ),
        )

    if isinstance(exc, httpx.HTTPStatusError):
        if exc.response.status_code == 404:
            return _translate_404(exc, context)
        return ErrorPayload(error=str(exc), code="http_error")

    if isinstance(exc, ValidationError):
        return ErrorPayload(error=str(exc), code="validation_failed")

    # Fallthrough: unknown exception. Preserve legacy behaviour (no code,
    # str(exc) as `error`).
    return ErrorPayload(error=str(exc))


def _translate_404(
    exc: httpx.HTTPStatusError, context: ErrorContext | None
) -> ErrorPayload:
    if context is None or context.tool is None or context.granularity is None:
        return ErrorPayload(error=str(exc), code="dataset_not_found")

    next_granularity = GRANULARITY_FALLBACK[context.granularity]
    if next_granularity is not None:
        repair = Repair(
            next_step="retry with the next granularity",
            tool=context.tool,
            arguments={"granularity": next_granularity},
        )
    else:
        repair = Repair(
            next_step="escalate to the user; no automated retry available",
            alternative=(
                "verify Local API is enabled on the sensor; if 1m is "
                "unavailable, lower granularities are unlikely to be enabled either"
            ),
        )
    return ErrorPayload(
        error=str(exc),
        code="granularity_unavailable",
        repair=repair,
    )
