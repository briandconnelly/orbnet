"""Error translation for the Orb MCP server.

A pure dispatch from raised exceptions (httpx transport errors, HTTP status
errors, Pydantic validation errors) to structured `ErrorPayload` envelopes
agents can branch on.

This module is import-light: it depends only on `models` for the types it
emits. The `translate_exception` function is added in a follow-up task; this
file currently exposes the lookup tables and the per-call context object.
"""

from pydantic import BaseModel, ConfigDict

from .models import Granularity

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
