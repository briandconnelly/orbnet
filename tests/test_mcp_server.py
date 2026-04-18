"""Tests for orbnet.mcp_server tool, prompt, and entry-point wiring.

These tests invoke the underlying functions of FastMCP-decorated tools and
prompts via their ``.fn`` attribute, patching ``get_client`` so no real
network calls are made.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from orbnet import mcp_server


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
    result = await mcp_server.get_scores_1m.fn(ctx, host="h")
    assert result == []
    mock_client.get_scores_1m.assert_awaited_once()
    ctx.info.assert_awaited_once()


async def test_get_responsiveness_tool(mock_client, ctx):
    result = await mcp_server.get_responsiveness.fn(ctx, host="h", granularity="1s")
    assert result == []
    mock_client.get_responsiveness.assert_awaited_once_with(granularity="1s")


async def test_get_web_responsiveness_tool(mock_client, ctx):
    result = await mcp_server.get_web_responsiveness.fn(ctx, host="h")
    assert result == []
    mock_client.get_web_responsiveness.assert_awaited_once()


async def test_get_speed_results_tool(mock_client, ctx):
    result = await mcp_server.get_speed_results.fn(ctx, host="h")
    assert result == []
    mock_client.get_speed_results.assert_awaited_once()


async def test_get_wifi_link_tool(mock_client, ctx):
    result = await mcp_server.get_wifi_link.fn(ctx, host="h", granularity="15s")
    assert result == []
    mock_client.get_wifi_link.assert_awaited_once_with(granularity="15s")


async def test_get_all_datasets_tool(mock_client, ctx):
    result = await mcp_server.get_all_datasets.fn(
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

    info = mcp_server.get_client_info.fn(host="h")
    assert info["host"] == "h"
    assert info["caller_id"] == "cid"


def test_analyze_network_quality_prompt():
    text = mcp_server.analyze_network_quality.fn()
    assert "get_scores_1m" in text


def test_troubleshoot_slow_internet_prompt():
    text = mcp_server.troubleshoot_slow_internet.fn()
    assert "get_speed_results" in text


def test_troubleshoot_wifi_prompt():
    text = mcp_server.troubleshoot_wifi.fn()
    assert "get_wifi_link" in text


def test_main_invokes_mcp_run(mocker):
    run = mocker.patch.object(mcp_server.mcp, "run")
    mcp_server.main()
    run.assert_called_once()
