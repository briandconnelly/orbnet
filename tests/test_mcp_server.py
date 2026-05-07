"""Tests for orbnet.mcp_server tool, prompt, and entry-point wiring.

These tests invoke FastMCP-decorated tools and prompts directly, patching
``get_client`` so no real network calls are made.
"""

import inspect
from unittest.mock import AsyncMock, MagicMock

import pytest

from orbnet import mcp_server
from orbnet.client import OrbAPIClient
from orbnet.models import AllDatasetsResponse, ErrorPayload


@pytest.fixture
def mock_client(mocker):
    """Patch get_client to return a MagicMock with async dataset methods."""
    client = MagicMock()
    client.get_scores_1m = AsyncMock(return_value=[])
    client.get_responsiveness = AsyncMock(return_value=[])
    client.get_web_responsiveness = AsyncMock(return_value=[])
    client.get_speed_results = AsyncMock(return_value=[])
    client.get_wifi_link = AsyncMock(return_value=[])
    client.get_all_datasets = AsyncMock(return_value={})
    mocker.patch.object(mcp_server, "get_client", return_value=client)
    return client


@pytest.fixture
def ctx():
    """Minimal Context stub with async info()."""
    c = MagicMock()
    c.info = AsyncMock()
    return c


async def test_orb_get_scores_tool(mock_client, ctx):
    result = await mcp_server.orb_get_scores(ctx, host="h")  # ty: ignore[unresolved-attribute]
    assert result == []
    mock_client.get_scores_1m.assert_awaited_once()
    ctx.info.assert_awaited_once()


async def test_orb_get_responsiveness_tool(mock_client, ctx):
    result = await mcp_server.orb_get_responsiveness(ctx, host="h", granularity="1s")  # ty: ignore[unresolved-attribute]  # noqa: E501
    assert result == []
    mock_client.get_responsiveness.assert_awaited_once_with(granularity="1s")


async def test_orb_get_web_responsiveness_tool(mock_client, ctx):
    result = await mcp_server.orb_get_web_responsiveness(ctx, host="h")  # ty: ignore[unresolved-attribute]
    assert result == []
    mock_client.get_web_responsiveness.assert_awaited_once()


async def test_orb_get_speed_results_tool(mock_client, ctx):
    result = await mcp_server.orb_get_speed_results(ctx, host="h")  # ty: ignore[unresolved-attribute]
    assert result == []
    mock_client.get_speed_results.assert_awaited_once()


async def test_orb_get_wifi_link_tool(mock_client, ctx):
    result = await mcp_server.orb_get_wifi_link(ctx, host="h", granularity="15s")  # ty: ignore[unresolved-attribute]
    assert result == []
    mock_client.get_wifi_link.assert_awaited_once_with(granularity="15s")


async def test_orb_get_all_datasets_tool(mock_client, ctx):
    result = await mcp_server.orb_get_all_datasets(
        ctx, host="h", include_all_responsiveness=True, include_all_wifi_link=True
    )
    assert result == {}
    mock_client.get_all_datasets.assert_awaited_once_with(
        include_all_responsiveness=True,
        include_all_wifi_link=True,
        default_granularity="1m",
    )


def test_orb_get_client_info_tool(mock_client):
    mock_client.host = "h"
    mock_client.port = 7080
    mock_client.base_url = "http://h:7080"
    mock_client.caller_id = "cid"
    mock_client.timeout = 30.0

    info = mcp_server.orb_get_client_info(host="h")
    assert info["host"] == "h"
    assert info["caller_id"] == "cid"


def test_analyze_network_quality_prompt():
    text = mcp_server.analyze_network_quality()
    assert isinstance(text, str)
    assert "orb_get_scores" in text


def test_troubleshoot_slow_internet_prompt():
    text = mcp_server.troubleshoot_slow_internet()
    assert isinstance(text, str)
    assert "orb_get_speed_results" in text


def test_troubleshoot_wifi_prompt():
    text = mcp_server.troubleshoot_wifi()
    assert isinstance(text, str)
    assert "orb_get_wifi_link" in text


def test_main_invokes_mcp_run(mocker):
    run = mocker.patch.object(mcp_server.mcp, "run")
    mcp_server.main()
    run.assert_called_once()


# ---------------------------------------------------------------------------
# Default-parity tests: MCP tool defaults must agree with client defaults.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("mcp_tool", "client_method"),
    [
        (mcp_server.orb_get_responsiveness, OrbAPIClient.get_responsiveness),  # ty: ignore[unresolved-attribute]
        (mcp_server.orb_get_wifi_link, OrbAPIClient.get_wifi_link),  # ty: ignore[unresolved-attribute]
    ],
)
def test_mcp_tool_granularity_default_matches_client(mcp_tool, client_method):
    mcp_default = inspect.signature(mcp_tool).parameters["granularity"].default
    client_default = inspect.signature(client_method).parameters["granularity"].default
    assert mcp_default == client_default, (
        f"{mcp_tool.__name__}(granularity=) defaults to {mcp_default!r} but "
        f"{client_method.__qualname__}(granularity=) defaults to {client_default!r}; "
        "MCP tool defaults must match the client to avoid silent behavior drift."
    )


async def test_orb_get_all_datasets_forwards_client_default_granularity(
    mock_client, ctx
):
    """orb_get_all_datasets does not currently expose default_granularity to MCP
    callers, so it must forward whatever the underlying client treats as default.
    This locks the MCP-layer hardcode to track the client default if either side
    moves.
    """
    await mcp_server.orb_get_all_datasets(ctx, host="h")
    call_kwargs = mock_client.get_all_datasets.await_args.kwargs
    client_default = (
        inspect.signature(OrbAPIClient.get_all_datasets)
        .parameters["default_granularity"]
        .default
    )
    assert call_kwargs["default_granularity"] == client_default


@pytest.mark.parametrize(
    ("mcp_tool", "client_method_attr"),
    [
        (mcp_server.orb_get_responsiveness, "get_responsiveness"),  # ty: ignore[unresolved-attribute]
        (mcp_server.orb_get_wifi_link, "get_wifi_link"),  # ty: ignore[unresolved-attribute]
    ],
)
async def test_mcp_tool_no_arg_forwards_client_default_granularity(
    mock_client, ctx, mcp_tool, client_method_attr
):
    """No-arg MCP call must forward the client's default granularity."""
    await mcp_tool(ctx, host="h")
    client_method = getattr(OrbAPIClient, client_method_attr)
    client_default = inspect.signature(client_method).parameters["granularity"].default
    forwarded = getattr(mock_client, client_method_attr).await_args.kwargs[
        "granularity"
    ]
    assert forwarded == client_default


def test_register_dataset_tool_raises_for_missing_client_method():
    """Registration-time invariant: the spec must reference an
    OrbAPIClient method that exists. Catches typos in spec.family or
    a registry entry added without a corresponding client method."""
    from dataclasses import replace

    from orbnet.datasets import DATASETS
    from orbnet.mcp_server import _register_dataset_tool
    from orbnet.models import ScoreRecord

    # Mutate scores spec to point at a nonexistent family name. The
    # factory derives client_method_name = f"get_{spec.family}" for
    # non-scores families.
    bogus_spec = replace(DATASETS["responsiveness"], family="bogus_family")

    with pytest.raises(RuntimeError, match="bogus_family"):
        _register_dataset_tool(
            bogus_spec,
            title="Bogus",
            tags={"orb"},
            docstring="bogus",
            granular=True,
            record_type=ScoreRecord,
        )


# ---------------------------------------------------------------------------
# Tool metadata tests (FastMCP 3.2: title, tags, ToolAnnotations)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("tool_name", "expected_title", "expected_tags"),
    [
        ("orb_get_scores", "Get Scores Dataset", {"orb", "scores"}),
        (
            "orb_get_responsiveness",
            "Get Responsiveness Dataset",
            {"orb", "responsiveness"},
        ),
        (
            "orb_get_web_responsiveness",
            "Get Web Responsiveness Dataset",
            {"orb", "web-performance"},
        ),
        ("orb_get_speed_results", "Get Speed Test Results", {"orb", "speed"}),
        ("orb_get_wifi_link", "Get Wi-Fi Link Dataset", {"orb", "wifi"}),
    ],
)
async def test_dataset_tool_metadata(tool_name, expected_title, expected_tags):
    tool = await mcp_server.mcp.get_tool(tool_name)
    assert tool is not None
    assert tool.title == expected_title
    assert tool.tags == expected_tags
    assert tool.annotations is not None
    assert tool.annotations.readOnlyHint is True
    assert tool.annotations.openWorldHint is True
    assert tool.annotations.idempotentHint is None


async def test_tool_metadata_orb_get_all_datasets():
    tool = await mcp_server.mcp.get_tool("orb_get_all_datasets")
    assert tool is not None
    assert tool.title == "Get All Datasets"
    assert tool.tags == {"orb", "aggregate"}
    assert tool.annotations is not None
    assert tool.annotations.readOnlyHint is True
    assert tool.annotations.openWorldHint is True
    assert tool.annotations.idempotentHint is None


async def test_tool_metadata_orb_get_client_info():
    tool = await mcp_server.mcp.get_tool("orb_get_client_info")
    assert tool is not None
    assert tool.title == "Get Client Configuration"
    assert tool.tags == {"orb", "config"}
    assert tool.annotations is not None
    assert tool.annotations.readOnlyHint is True
    assert tool.annotations.openWorldHint is False
    assert tool.annotations.idempotentHint is None


# ---------------------------------------------------------------------------
# Prompt metadata tests (FastMCP 3.2: title, tags)
# ---------------------------------------------------------------------------


async def test_prompt_metadata_analyze_network_quality():
    prompt = await mcp_server.mcp.get_prompt("analyze_network_quality")
    assert prompt is not None
    assert prompt.title == "Analyze Network Quality"
    assert prompt.tags == {"orb", "analysis"}


async def test_prompt_metadata_troubleshoot_slow_internet():
    prompt = await mcp_server.mcp.get_prompt("troubleshoot_slow_internet")
    assert prompt is not None
    assert prompt.title == "Troubleshoot Slow Internet"
    assert prompt.tags == {"orb", "speed", "troubleshooting"}


async def test_prompt_metadata_troubleshoot_wifi():
    prompt = await mcp_server.mcp.get_prompt("troubleshoot_wifi")
    assert prompt is not None
    assert prompt.title == "Troubleshoot Wi-Fi"
    assert prompt.tags == {"orb", "wifi", "troubleshooting"}


async def test_registered_tools_and_prompts():
    tools = await mcp_server.mcp.list_tools()
    prompts = await mcp_server.mcp.list_prompts()
    assert {t.name for t in tools} == {
        "orb_get_scores",
        "orb_get_responsiveness",
        "orb_get_web_responsiveness",
        "orb_get_speed_results",
        "orb_get_wifi_link",
        "orb_get_all_datasets",
        "orb_get_client_info",
    }
    assert {p.name for p in prompts} == {
        "analyze_network_quality",
        "troubleshoot_slow_internet",
        "troubleshoot_wifi",
    }


async def test_orb_get_all_datasets_error_payload_passthrough(mock_client, ctx):
    error_payload = ErrorPayload(error="connection refused")
    response = AllDatasetsResponse(
        scores_1m=[],
        responsiveness_1s=error_payload,
        web_responsiveness=[],
        speed_results=[],
    )
    mock_client.get_all_datasets = AsyncMock(return_value=response)

    result = await mcp_server.orb_get_all_datasets(ctx, host="h")

    assert isinstance(result, AllDatasetsResponse)
    # exclude_none preserves the legacy bare error wire format; the
    # extended ErrorPayload's optional code/repair default to None and
    # are omitted.
    dumped = result.model_dump(exclude_none=True)
    assert dumped["responsiveness_1s"] == {"error": "connection refused"}
    assert dumped["scores_1m"] == []
    mock_client.get_all_datasets.assert_awaited_once_with(
        include_all_responsiveness=False,
        include_all_wifi_link=False,
        default_granularity="1m",
    )


class TestGetClientOverrideSemantics:
    """get_client uses `is None` checks so that explicit values like port=0 reach
    the OrbAPIClient/Pydantic layer (where they get rejected) instead of being
    silently replaced by the env-derived defaults."""

    def test_port_zero_reaches_pydantic_validation(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            mcp_server.get_client(host="h", port=0)

    def test_timeout_zero_reaches_pydantic_validation(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            mcp_server.get_client(host="h", timeout=0.0)

    def test_explicit_caller_id_empty_string_passes_through(self):
        client = mcp_server.get_client(host="h", caller_id="")
        assert client.caller_id == ""

    def test_empty_host_is_rejected(self):
        """host="" would produce an invalid base URL; reject at validation."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            mcp_server.get_client(host="")


async def test_log_uses_resolved_host_not_raw_arg(mock_client, ctx):
    """When host is None, the log message should report the resolved host
    (from config), not literal 'None'."""
    mock_client.host = "resolved-host"

    await mcp_server.orb_get_scores(ctx, host=None)  # ty: ignore[unresolved-attribute]

    ctx.info.assert_awaited_once()
    log_message = ctx.info.await_args.args[0]
    assert "resolved-host" in log_message
    assert "None" not in log_message


class TestLazyConfigLoading:
    """Config is loaded lazily on first access (not at import time), so tests
    can set ORB_HOST/ORB_PORT/ORB_TIMEOUT before first use without import-order
    coupling. Cached after first call."""

    def setup_method(self):
        mcp_server.get_config.cache_clear()

    def teardown_method(self):
        mcp_server.get_config.cache_clear()

    def test_env_vars_set_before_first_call_are_honored(self, monkeypatch):
        monkeypatch.setenv("ORB_HOST", "lazy-host.example.com")
        monkeypatch.setenv("ORB_PORT", "9999")
        monkeypatch.setenv("ORB_TIMEOUT", "12.5")

        cfg = mcp_server.get_config()

        assert cfg.host == "lazy-host.example.com"
        assert cfg.port == 9999
        assert cfg.timeout == 12.5

    def test_repeated_calls_return_same_cached_instance(self):
        first = mcp_server.get_config()
        second = mcp_server.get_config()
        assert first is second


# ---------------------------------------------------------------------------
# Discoverability surface:
#   - Server instructions carry only client-actionable information: stateful
#     polling semantics and explicit negative scope (no transport/auth/env-var
#     declarations — those don't help an agent that has already connected).
#   - get_client_info exposes a server fingerprint.
#   - Prompts list prerequisites and avoid duplicating model-level platform
#     notes.
# ---------------------------------------------------------------------------


class TestServerInstructions:
    """The instructions block is what an MCP client reads at cold start. It
    must carry the client-actionable bits (stateful-polling behavior and
    negative scope) without leaking server-operator metadata an agent
    can't act on.
    """

    @pytest.fixture
    def text(self):
        return mcp_server.mcp.instructions or ""

    @pytest.mark.parametrize(
        "anchor",
        [
            "Stateful polling:",
            "Does NOT",
        ],
    )
    def test_declares_section(self, text, anchor):
        assert anchor in text, f"server instructions should declare '{anchor}'"

    def test_stateful_polling_describes_substantive_behavior(self, text):
        """Header presence is necessary but not sufficient — the section must
        carry the behavior agents need to interpret repeated tool calls
        correctly. Pin the load-bearing tokens against wording regressions."""
        assert "caller_id" in text
        assert "only new" in text


class TestOrbGetClientInfoFingerprint:
    """orb_get_client_info should surface the server fingerprint so agents that
    skip the instructions block can still discover the version they're against.
    """

    def test_response_includes_server_fingerprint(self, mock_client):
        from orbnet import __version__

        mock_client.host = "h"
        mock_client.port = 7080
        mock_client.base_url = "http://h:7080"
        mock_client.caller_id = "cid"
        mock_client.timeout = 30.0

        info = mcp_server.orb_get_client_info(host="h")

        assert info["server_fingerprint"] == f"orbnet@{__version__}"


class TestPromptPrerequisites:
    """Each prompt should declare its prerequisites so agents can fail fast
    with a clear message instead of mid-execution.
    """

    @pytest.mark.parametrize(
        "prompt_fn",
        [
            mcp_server.analyze_network_quality,
            mcp_server.troubleshoot_slow_internet,
            mcp_server.troubleshoot_wifi,
        ],
    )
    def test_prompt_declares_prerequisites(self, prompt_fn):
        text = prompt_fn()
        assert "Prerequisites:" in text


class TestTroubleshootWifiNoPlatformDuplication:
    """troubleshoot_wifi previously embedded platform-availability notes
    (macOS / Android / Linux / Windows) that duplicate WifiLinkRecord's
    docstring. Drop them to keep the prompt as orchestration scaffolding,
    not a redundant copy of the schema-level contract.
    """

    @pytest.mark.parametrize("platform", ["macOS", "Android", "Linux", "Windows"])
    def test_does_not_mention_platform(self, platform):
        text = mcp_server.troubleshoot_wifi()
        assert platform not in text, (
            f"troubleshoot_wifi should not duplicate WifiLinkRecord's "
            f"platform-availability notes ('{platform}' found in prompt text)"
        )


# ---------------------------------------------------------------------------
# Per-tool error envelope: widened return type + structured ErrorPayload
# ---------------------------------------------------------------------------


class TestOrbGetScoresErrorEnvelope:
    async def test_returns_error_payload_on_connect_error(self, mock_client, ctx):
        import httpx

        mock_client.get_scores_1m.side_effect = httpx.ConnectError("conn refused")

        result = await mcp_server.orb_get_scores(ctx, host="h")  # ty: ignore[unresolved-attribute]

        assert isinstance(result, ErrorPayload)
        assert result.code == "sensor_unreachable"
        assert result.repair is not None


class TestOrbGetResponsivenessErrorEnvelope:
    async def test_404_at_1s_suggests_15s(self, mock_client, ctx):
        import httpx

        request = httpx.Request(
            "GET", "http://h:7080/api/v2/datasets/responsiveness_1s.json"
        )
        response = httpx.Response(404, request=request)
        mock_client.get_responsiveness.side_effect = httpx.HTTPStatusError(
            "404", request=request, response=response
        )

        result = await mcp_server.orb_get_responsiveness(  # ty: ignore[unresolved-attribute]
            ctx, host="h", granularity="1s"
        )

        assert isinstance(result, ErrorPayload)
        assert result.code == "granularity_unavailable"
        assert result.repair is not None
        assert result.repair.tool == "orb_get_responsiveness"
        assert result.repair.arguments == {"granularity": "15s"}

    async def test_404_at_1m_populates_alternative(self, mock_client, ctx):
        import httpx

        request = httpx.Request(
            "GET", "http://h:7080/api/v2/datasets/responsiveness_1m.json"
        )
        response = httpx.Response(404, request=request)
        mock_client.get_responsiveness.side_effect = httpx.HTTPStatusError(
            "404", request=request, response=response
        )

        result = await mcp_server.orb_get_responsiveness(  # ty: ignore[unresolved-attribute]
            ctx, host="h", granularity="1m"
        )

        assert isinstance(result, ErrorPayload)
        assert result.code == "granularity_unavailable"
        assert result.repair is not None
        assert result.repair.arguments is None
        assert result.repair.alternative is not None


class TestOrbGetWifiLinkErrorEnvelope:
    async def test_404_at_1s_suggests_15s(self, mock_client, ctx):
        import httpx

        request = httpx.Request(
            "GET", "http://h:7080/api/v2/datasets/wifi_link_1s.json"
        )
        response = httpx.Response(404, request=request)
        mock_client.get_wifi_link.side_effect = httpx.HTTPStatusError(
            "404", request=request, response=response
        )

        result = await mcp_server.orb_get_wifi_link(ctx, host="h", granularity="1s")  # ty: ignore[unresolved-attribute]

        assert isinstance(result, ErrorPayload)
        assert result.code == "granularity_unavailable"
        assert result.repair is not None
        assert result.repair.tool == "orb_get_wifi_link"
        assert result.repair.arguments == {"granularity": "15s"}


class TestOrbGetWebResponsivenessErrorEnvelope:
    async def test_404_is_dataset_not_found(self, mock_client, ctx):
        import httpx

        request = httpx.Request(
            "GET", "http://h:7080/api/v2/datasets/web_responsiveness_results.json"
        )
        response = httpx.Response(404, request=request)
        mock_client.get_web_responsiveness.side_effect = httpx.HTTPStatusError(
            "404", request=request, response=response
        )

        result = await mcp_server.orb_get_web_responsiveness(ctx, host="h")  # ty: ignore[unresolved-attribute]

        assert isinstance(result, ErrorPayload)
        assert result.code == "dataset_not_found"


class TestOrbGetSpeedResultsErrorEnvelope:
    async def test_timeout_emits_timeout_code(self, mock_client, ctx):
        import httpx

        mock_client.get_speed_results.side_effect = httpx.TimeoutException("slow")

        result = await mcp_server.orb_get_speed_results(ctx, host="h")  # ty: ignore[unresolved-attribute]

        assert isinstance(result, ErrorPayload)
        assert result.code == "timeout"


class TestMCPOutputSchemaIsUnion:
    """FastMCP derives outputSchema from each tool's return-type annotation.
    After widening to `list[X] | ErrorPayload`, the schema must accept both
    branches — pin this so MCP clients see an additive shape change rather
    than a regression."""

    @pytest.mark.parametrize(
        "tool_name",
        [
            "orb_get_scores",
            "orb_get_responsiveness",
            "orb_get_wifi_link",
            "orb_get_web_responsiveness",
            "orb_get_speed_results",
            # Other widened tools added in later tasks.
        ],
    )
    async def test_output_schema_accepts_array_or_error_payload(self, tool_name: str):
        tool = await mcp_server.mcp.get_tool(tool_name)
        assert tool is not None
        schema = tool.output_schema
        assert schema is not None, f"{tool_name} has no output schema"

        # Pydantic emits unions as `anyOf`. Look for a union-shaped top level
        # OR a wrapped union one level deep; FastMCP wraps result schemas
        # with a `result` key in some versions.
        candidates = [schema]
        if "properties" in schema and "result" in schema["properties"]:
            candidates.append(schema["properties"]["result"])

        # Require not just *a* union node, but a union with >=2 branches. A
        # regression where FastMCP/Pydantic collapsed the union to a single
        # `anyOf: [<one>]` would pass the bare-existence check silently.
        def _union_branches(c: dict) -> int:
            for key in ("anyOf", "oneOf"):
                if key in c and isinstance(c[key], list):
                    return len(c[key])
            return 0

        best = max((_union_branches(c) for c in candidates), default=0)
        assert best >= 2, (
            f"{tool_name} output schema is not a multi-branch union "
            f"(best union arity: {best}): {schema}"
        )


async def test_old_tool_names_are_not_registered():
    """The hard rename to orb_get_* must not leave the old names
    discoverable. PR 4's rationale assumes a clean surface — a residual
    old-name registration would silently undo that."""
    tools = await mcp_server.mcp.list_tools()
    names = {t.name for t in tools}
    old_names = {
        "get_scores_1m",
        "get_responsiveness",
        "get_web_responsiveness",
        "get_speed_results",
        "get_wifi_link",
        "get_all_datasets",
        "get_client_info",
    }
    assert names.isdisjoint(old_names), (
        f"old tool names still registered: {names & old_names}"
    )
