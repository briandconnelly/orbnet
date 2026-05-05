"""Tests for orbnet.mcp_server tool, prompt, and entry-point wiring.

These tests invoke FastMCP-decorated tools and prompts directly, patching
``get_client`` so no real network calls are made.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from orbnet import mcp_server
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


async def test_get_scores_1m_tool(mock_client, ctx):
    result = await mcp_server.get_scores_1m(ctx, host="h")
    assert result == []
    mock_client.get_scores_1m.assert_awaited_once()
    ctx.info.assert_awaited_once()


async def test_get_responsiveness_tool(mock_client, ctx):
    result = await mcp_server.get_responsiveness(ctx, host="h", granularity="1s")
    assert result == []
    mock_client.get_responsiveness.assert_awaited_once_with(granularity="1s")


async def test_get_web_responsiveness_tool(mock_client, ctx):
    result = await mcp_server.get_web_responsiveness(ctx, host="h")
    assert result == []
    mock_client.get_web_responsiveness.assert_awaited_once()


async def test_get_speed_results_tool(mock_client, ctx):
    result = await mcp_server.get_speed_results(ctx, host="h")
    assert result == []
    mock_client.get_speed_results.assert_awaited_once()


async def test_get_wifi_link_tool(mock_client, ctx):
    result = await mcp_server.get_wifi_link(ctx, host="h", granularity="15s")
    assert result == []
    mock_client.get_wifi_link.assert_awaited_once_with(granularity="15s")


async def test_get_all_datasets_tool(mock_client, ctx):
    result = await mcp_server.get_all_datasets(
        ctx, host="h", include_all_responsiveness=True, include_all_wifi_link=True
    )
    assert result == {}
    mock_client.get_all_datasets.assert_awaited_once_with(
        include_all_responsiveness=True,
        include_all_wifi_link=True,
        default_granularity="1s",
    )


def test_get_client_info_tool(mock_client):
    mock_client.host = "h"
    mock_client.port = 7080
    mock_client.base_url = "http://h:7080"
    mock_client.caller_id = "cid"
    mock_client.timeout = 30.0

    info = mcp_server.get_client_info(host="h")
    assert info["host"] == "h"
    assert info["caller_id"] == "cid"


def test_analyze_network_quality_prompt():
    text = mcp_server.analyze_network_quality()
    assert isinstance(text, str)
    assert "get_scores_1m" in text


def test_troubleshoot_slow_internet_prompt():
    text = mcp_server.troubleshoot_slow_internet()
    assert isinstance(text, str)
    assert "get_speed_results" in text


def test_troubleshoot_wifi_prompt():
    text = mcp_server.troubleshoot_wifi()
    assert isinstance(text, str)
    assert "get_wifi_link" in text


def test_main_invokes_mcp_run(mocker):
    run = mocker.patch.object(mcp_server.mcp, "run")
    mcp_server.main()
    run.assert_called_once()


# ---------------------------------------------------------------------------
# Tool metadata tests (FastMCP 3.2: title, tags, ToolAnnotations)
# ---------------------------------------------------------------------------


async def test_tool_metadata_get_scores_1m():
    tool = await mcp_server.mcp.get_tool("get_scores_1m")
    assert tool is not None
    assert tool.title == "Get Scores Dataset (1m)"
    assert tool.tags == {"orb", "scores"}
    assert tool.annotations is not None
    assert tool.annotations.readOnlyHint is True
    assert tool.annotations.openWorldHint is True
    assert tool.annotations.idempotentHint is None


async def test_tool_metadata_get_responsiveness():
    tool = await mcp_server.mcp.get_tool("get_responsiveness")
    assert tool is not None
    assert tool.title == "Get Responsiveness Dataset"
    assert tool.tags == {"orb", "responsiveness"}
    assert tool.annotations is not None
    assert tool.annotations.readOnlyHint is True
    assert tool.annotations.openWorldHint is True
    assert tool.annotations.idempotentHint is None


async def test_tool_metadata_get_web_responsiveness():
    tool = await mcp_server.mcp.get_tool("get_web_responsiveness")
    assert tool is not None
    assert tool.title == "Get Web Responsiveness Dataset"
    assert tool.tags == {"orb", "web-performance"}
    assert tool.annotations is not None
    assert tool.annotations.readOnlyHint is True
    assert tool.annotations.openWorldHint is True
    assert tool.annotations.idempotentHint is None


async def test_tool_metadata_get_speed_results():
    tool = await mcp_server.mcp.get_tool("get_speed_results")
    assert tool is not None
    assert tool.title == "Get Speed Test Results"
    assert tool.tags == {"orb", "speed"}
    assert tool.annotations is not None
    assert tool.annotations.readOnlyHint is True
    assert tool.annotations.openWorldHint is True
    assert tool.annotations.idempotentHint is None


async def test_tool_metadata_get_wifi_link():
    tool = await mcp_server.mcp.get_tool("get_wifi_link")
    assert tool is not None
    assert tool.title == "Get Wi-Fi Link Dataset"
    assert tool.tags == {"orb", "wifi"}
    assert tool.annotations is not None
    assert tool.annotations.readOnlyHint is True
    assert tool.annotations.openWorldHint is True
    assert tool.annotations.idempotentHint is None


async def test_tool_metadata_get_all_datasets():
    tool = await mcp_server.mcp.get_tool("get_all_datasets")
    assert tool is not None
    assert tool.title == "Get All Datasets"
    assert tool.tags == {"orb", "aggregate"}
    assert tool.annotations is not None
    assert tool.annotations.readOnlyHint is True
    assert tool.annotations.openWorldHint is True
    assert tool.annotations.idempotentHint is None


async def test_tool_metadata_get_client_info():
    tool = await mcp_server.mcp.get_tool("get_client_info")
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
        "get_scores_1m",
        "get_responsiveness",
        "get_web_responsiveness",
        "get_speed_results",
        "get_wifi_link",
        "get_all_datasets",
        "get_client_info",
    }
    assert {p.name for p in prompts} == {
        "analyze_network_quality",
        "troubleshoot_slow_internet",
        "troubleshoot_wifi",
    }


async def test_get_all_datasets_error_payload_passthrough(mock_client, ctx):
    error_payload = ErrorPayload(error="connection refused")
    response = AllDatasetsResponse(
        scores_1m=[],
        responsiveness_1s=error_payload,
        web_responsiveness=[],
        speed_results=[],
    )
    mock_client.get_all_datasets = AsyncMock(return_value=response)

    result = await mcp_server.get_all_datasets(ctx, host="h")

    assert isinstance(result, AllDatasetsResponse)
    dumped = result.model_dump()
    assert dumped["responsiveness_1s"] == {"error": "connection refused"}
    assert dumped["scores_1m"] == []
    mock_client.get_all_datasets.assert_awaited_once_with(
        include_all_responsiveness=False,
        include_all_wifi_link=False,
        default_granularity="1s",
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


async def test_log_uses_resolved_host_not_raw_arg(mock_client, ctx):
    """When host is None, the log message should report the resolved host
    (from config), not literal 'None'."""
    mock_client.host = "resolved-host"

    await mcp_server.get_scores_1m(ctx, host=None)

    ctx.info.assert_awaited_once()
    log_message = ctx.info.await_args.args[0]
    assert "resolved-host" in log_message
    assert "None" not in log_message
