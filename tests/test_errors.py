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
    def test_scores_family_maps_to_orb_get_scores(self):
        assert FAMILY_TO_TOOL_NAME["scores"] == "orb_get_scores"

    @pytest.mark.parametrize(
        "family",
        ["responsiveness", "web_responsiveness", "speed_results", "wifi_link"],
    )
    def test_other_families_round_trip(self, family: str):
        assert FAMILY_TO_TOOL_NAME[family] == f"orb_get_{family}"


class TestErrorContext:
    def test_defaults_to_all_none(self):
        ctx = ErrorContext()
        assert ctx.tool is None
        assert ctx.granularity is None

    def test_extra_fields_forbidden(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ErrorContext(tool="orb_get_responsiveness", bogus="x")  # type: ignore[call-arg]  # ty: ignore[unknown-argument]


# ---------------------------------------------------------------------------
# translate_exception dispatch
# ---------------------------------------------------------------------------


class TestTranslateExceptionDispatch:
    """Pin every dispatch branch in translate_exception. First match wins;
    order matches the spec's §Translation."""

    def test_connect_error_is_sensor_unreachable(self):
        from orbnet.errors import translate_exception

        payload = translate_exception(httpx.ConnectError("conn refused"))
        assert payload.code == "sensor_unreachable"
        assert payload.repair is not None
        assert "Local API" in payload.repair.next_step
        assert payload.repair.alternative is not None
        assert "ORB_HOST" in payload.repair.alternative

    def test_network_error_is_sensor_unreachable(self):
        from orbnet.errors import translate_exception

        payload = translate_exception(httpx.NetworkError("network down"))
        assert payload.code == "sensor_unreachable"

    def test_timeout_exception_is_timeout(self):
        from orbnet.errors import translate_exception

        payload = translate_exception(httpx.TimeoutException("slow"))
        assert payload.code == "timeout"
        assert payload.repair is not None
        assert "timeout" in payload.repair.next_step.lower()

    def test_404_without_context_is_dataset_not_found(self):
        from orbnet.errors import translate_exception

        payload = translate_exception(_make_status_error(404), context=None)
        assert payload.code == "dataset_not_found"

    def test_404_with_tool_but_no_granularity_is_dataset_not_found(self):
        from orbnet.errors import translate_exception

        ctx = ErrorContext(tool="orb_get_speed_results")
        payload = translate_exception(_make_status_error(404), context=ctx)
        assert payload.code == "dataset_not_found"

    def test_500_is_http_error(self):
        from orbnet.errors import translate_exception

        payload = translate_exception(_make_status_error(500))
        assert payload.code == "http_error"

    def test_validation_error_is_validation_failed(self):
        from pydantic import TypeAdapter, ValidationError

        from orbnet.errors import translate_exception

        try:
            TypeAdapter(int).validate_python("not-an-int")
        except ValidationError as exc:
            payload = translate_exception(exc)
        assert payload.code == "validation_failed"
        assert payload.repair is None  # no machine-actionable repair

    def test_unknown_exception_falls_through(self):
        from orbnet.errors import translate_exception

        payload = translate_exception(RuntimeError("surprise"))
        assert payload.code is None
        assert payload.repair is None
        assert "surprise" in payload.error


class TestGranularityRepairChain:
    """When a 404 happens on a granular tool, the repair hint must point to
    the next granularity in the fallback chain. When the failed granularity
    is the last in the chain (1m), `repair.alternative` carries the
    escalation cue rather than `repair = None`."""

    @pytest.mark.parametrize(
        ("failed", "expected_next"),
        [("1s", "15s"), ("15s", "1m")],
    )
    def test_404_with_granular_context_suggests_next(
        self, failed: Granularity, expected_next: Granularity
    ):
        from orbnet.errors import translate_exception

        ctx = ErrorContext(tool="orb_get_responsiveness", granularity=failed)
        payload = translate_exception(_make_status_error(404), context=ctx)

        assert payload.code == "granularity_unavailable"
        assert payload.repair is not None
        assert payload.repair.tool == "orb_get_responsiveness"
        assert payload.repair.arguments == {"granularity": expected_next}
        assert payload.repair.alternative is None

    def test_404_at_last_granularity_populates_alternative(self):
        from orbnet.errors import translate_exception

        ctx = ErrorContext(tool="orb_get_responsiveness", granularity="1m")
        payload = translate_exception(_make_status_error(404), context=ctx)

        assert payload.code == "granularity_unavailable"
        assert payload.repair is not None
        assert payload.repair.tool is None
        assert payload.repair.arguments is None
        assert payload.repair.alternative is not None
        assert "Local API" in payload.repair.alternative
