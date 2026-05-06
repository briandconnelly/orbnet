"""Tests for orbnet.transport — the HTTP adapter at the dataset-fetch seam.

These are the only tests that mock httpx directly. Everywhere else in the
suite, OrbAPIClient is constructed with a FakeDatasetTransport instead.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from orbnet.transport import HttpxDatasetTransport


@pytest.fixture
def mock_httpx_response():
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json = MagicMock(return_value=[])
    return response


class TestHttpxDatasetTransport:
    @pytest.mark.asyncio
    async def test_fetch_builds_correct_url(self, mock_httpx_response):
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_httpx_response

            transport = HttpxDatasetTransport(
                host="192.168.1.100",
                port=7080,
                client_id="orbnet/test",
                timeout=30.0,
            )
            await transport.fetch_dataset("scores_1m", {"id": "caller-x"})

            call_args = mock_client.get.call_args
            assert (
                call_args[0][0]
                == "http://192.168.1.100:7080/api/v2/datasets/scores_1m.json"
            )

    @pytest.mark.asyncio
    async def test_fetch_sets_user_agent_from_client_id(self, mock_httpx_response):
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_httpx_response

            transport = HttpxDatasetTransport(
                host="h",
                port=7080,
                client_id="my-app/1.2",
                timeout=30.0,
            )
            await transport.fetch_dataset("scores_1m", {"id": "x"})

            headers = mock_client.get.call_args[1]["headers"]
            assert headers == {"Accept": "application/json", "User-Agent": "my-app/1.2"}

    @pytest.mark.asyncio
    async def test_fetch_passes_params_through(self, mock_httpx_response):
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_httpx_response

            transport = HttpxDatasetTransport(
                host="h",
                port=7080,
                client_id="ua",
                timeout=30.0,
            )
            await transport.fetch_dataset(
                "responsiveness_1s", {"id": "c", "start_time": 123, "end_time": 456}
            )

            params = mock_client.get.call_args[1]["params"]
            assert params == {"id": "c", "start_time": 123, "end_time": 456}

    @pytest.mark.asyncio
    async def test_fetch_returns_parsed_json(self, mock_httpx_response):
        mock_httpx_response.json.return_value = [{"orb_id": "x"}]
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_httpx_response

            transport = HttpxDatasetTransport(
                host="h",
                port=7080,
                client_id="ua",
                timeout=30.0,
            )
            result = await transport.fetch_dataset("scores_1m", {"id": "x"})

            assert result == [{"orb_id": "x"}]

    @pytest.mark.asyncio
    async def test_fetch_raises_on_http_status_error(self, mock_httpx_response):
        mock_httpx_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404",
            request=MagicMock(),
            response=mock_httpx_response,
        )
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_httpx_response

            transport = HttpxDatasetTransport(
                host="h",
                port=7080,
                client_id="ua",
                timeout=30.0,
            )
            with pytest.raises(httpx.HTTPStatusError):
                await transport.fetch_dataset("scores_1m", {"id": "x"})

    @pytest.mark.asyncio
    async def test_fetch_uses_configured_timeout(self, mock_httpx_response):
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_httpx_response

            transport = HttpxDatasetTransport(
                host="h",
                port=7080,
                client_id="ua",
                timeout=12.5,
            )
            await transport.fetch_dataset("scores_1m", {"id": "x"})

            init_kwargs = mock_client_class.call_args[1]
            assert init_kwargs["timeout"] == 12.5
