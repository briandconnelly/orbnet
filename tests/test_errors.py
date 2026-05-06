"""Tests for orbnet.errors translation logic.

Pure unit tests on the dispatch from raised exceptions to ErrorPayload —
no I/O, no FastMCP wiring.
"""

import httpx
import pytest

from orbnet.errors import (
    FAMILY_TO_TOOL_NAME,
    GRANULARITY_FALLBACK,
    ErrorContext,
)
from orbnet.models import Granularity

# ---------------------------------------------------------------------------
# Helpers for constructing httpx exceptions in tests
# ---------------------------------------------------------------------------


def _make_status_error(
    status: int,
    url: str = "http://localhost:7080/api/v2/datasets/responsiveness_1s.json",
) -> httpx.HTTPStatusError:
    """Build an `httpx.HTTPStatusError` with a populated request and response.

    httpx's status errors carry both objects on the exception, and downstream
    code (and the translator we'll write next) reads `.response.status_code`
    to dispatch.
    """
    request = httpx.Request("GET", url)
    response = httpx.Response(status, request=request)
    return httpx.HTTPStatusError(f"{status} status", request=request, response=response)


# ---------------------------------------------------------------------------
# Helper sanity check
# ---------------------------------------------------------------------------


class TestMakeStatusErrorHelper:
    """Sanity check for the helper used by Task 3's translation tests.
    Without this, the helper is dead code in this commit."""

    def test_carries_status_code_request_and_response(self):
        err = _make_status_error(404)
        assert err.response.status_code == 404
        assert err.request.method == "GET"
        assert "/datasets/responsiveness_1s.json" in str(err.request.url)

    def test_accepts_custom_url(self):
        err = _make_status_error(500, url="http://other:1234/api/x.json")
        assert err.response.status_code == 500
        assert "http://other:1234/api/x.json" in str(err.request.url)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestGranularityFallbackChain:
    @pytest.mark.parametrize(
        ("current", "expected_next"),
        [("1s", "15s"), ("15s", "1m"), ("1m", None)],
    )
    def test_chain_advances(self, current: Granularity, expected_next):
        assert GRANULARITY_FALLBACK[current] == expected_next

    def test_chain_keys_match_granularity_literal(self):
        """When the Granularity literal grows, the fallback chain must keep up.

        Compares against the literal's runtime args so a bare addition to
        Granularity (without updating GRANULARITY_FALLBACK) trips this test.
        """
        from typing import get_args

        from orbnet.models import Granularity

        granularity_values = set(get_args(Granularity.__value__))
        assert set(GRANULARITY_FALLBACK.keys()) == granularity_values


class TestFamilyToToolName:
    def test_scores_family_maps_to_versioned_name(self):
        assert FAMILY_TO_TOOL_NAME["scores"] == "get_scores_1m"

    @pytest.mark.parametrize(
        "family",
        ["responsiveness", "web_responsiveness", "speed_results", "wifi_link"],
    )
    def test_other_families_round_trip(self, family: str):
        assert FAMILY_TO_TOOL_NAME[family] == f"get_{family}"


class TestErrorContext:
    def test_defaults_to_all_none(self):
        ctx = ErrorContext()
        assert ctx.tool is None
        assert ctx.granularity is None

    def test_extra_fields_forbidden(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ErrorContext(tool="get_responsiveness", bogus="x")  # type: ignore[call-arg]  # ty: ignore[unknown-argument]
