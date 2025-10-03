"""
Tests for OrbAPIClient in orbnet.client.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from orbnet.client import OrbAPIClient


class TestOrbAPIClient:
    """Test OrbAPIClient class."""

    def test_init_default_values(self):
        """Test client initialization with default values."""
        client = OrbAPIClient(host="192.168.1.100")
        assert client.host == "192.168.1.100"
        assert client.port == 7080
        assert client.caller_id is not None  # Should generate UUID
        assert client.client_id.startswith("orbnet/")
        assert client.timeout == 30.0

    def test_init_custom_values(self):
        """Test client initialization with custom values."""
        client = OrbAPIClient(
            host="192.168.1.100",
            port=8080,
            caller_id="test-caller",
            client_id="test-client",
            timeout=60.0,
        )
        assert client.host == "192.168.1.100"
        assert client.port == 8080
        assert client.caller_id == "test-caller"
        assert client.client_id == "test-client"
        assert client.timeout == 60.0

    def test_base_url_property(self):
        """Test base_url property construction."""
        client = OrbAPIClient(host="example.com", port=9000)
        assert client.base_url == "http://example.com:9000"

    def test_get_headers(self):
        """Test _get_headers method."""
        client = OrbAPIClient(host="192.168.1.100", client_id="test-client")
        headers = client._get_headers()
        assert headers == {
            "Accept": "application/json",
            "User-Agent": "test-client",
        }

    @pytest.mark.asyncio
    async def test_get_dataset_json_format(
        self, sample_scores_data, mock_httpx_response
    ):
        """Test _get_dataset with JSON format."""
        mock_httpx_response.json.return_value = sample_scores_data

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_httpx_response

            client = OrbAPIClient(host="192.168.1.100")
            result = await client._get_dataset("scores_1m", format="json")

            assert result == sample_scores_data
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert "scores_1m.json" in call_args[0][0]
            assert call_args[1]["params"]["id"] == client.caller_id

    @pytest.mark.asyncio
    async def test_get_dataset_jsonl_format(
        self, sample_jsonl_data, mock_httpx_response
    ):
        """Test _get_dataset with JSONL format."""
        mock_httpx_response.text = sample_jsonl_data

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_httpx_response

            client = OrbAPIClient(host="192.168.1.100")
            result = await client._get_dataset("scores_1m", format="jsonl")

            assert result == sample_jsonl_data
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert "scores_1m.jsonl" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_dataset_with_custom_caller_id(
        self, sample_scores_data, mock_httpx_response
    ):
        """Test _get_dataset with custom caller_id."""
        mock_httpx_response.json.return_value = sample_scores_data

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_httpx_response

            client = OrbAPIClient(host="192.168.1.100")
            result = await client._get_dataset(
                "scores_1m", format="json", caller_id="custom-caller"
            )

            assert result == sample_scores_data
            call_args = mock_client.get.call_args
            assert call_args[1]["params"]["id"] == "custom-caller"

    @pytest.mark.asyncio
    async def test_get_dataset_with_extra_params(
        self, sample_scores_data, mock_httpx_response
    ):
        """Test _get_dataset with extra parameters."""
        mock_httpx_response.json.return_value = sample_scores_data

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_httpx_response

            client = OrbAPIClient(host="192.168.1.100")
            result = await client._get_dataset(
                "scores_1m",
                format="json",
                start_time=1700000000000,
                end_time=1700000060000,
            )

            assert result == sample_scores_data
            call_args = mock_client.get.call_args
            params = call_args[1]["params"]
            assert params["start_time"] == 1700000000000
            assert params["end_time"] == 1700000060000

    @pytest.mark.asyncio
    async def test_get_dataset_http_error(self, mock_httpx_response):
        """Test _get_dataset with HTTP error."""
        mock_httpx_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=MagicMock(), response=mock_httpx_response
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_httpx_response

            client = OrbAPIClient(host="192.168.1.100")

            with pytest.raises(httpx.HTTPStatusError):
                await client._get_dataset("scores_1m", format="json")

    @pytest.mark.asyncio
    async def test_get_scores_1m(self, sample_scores_data, mock_httpx_response):
        """Test get_scores_1m method."""
        mock_httpx_response.json.return_value = sample_scores_data

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_httpx_response

            client = OrbAPIClient(host="192.168.1.100")
            result = await client.get_scores_1m()

            assert result == sample_scores_data
            call_args = mock_client.get.call_args
            assert "scores_1m.json" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_scores_1m_jsonl(self, sample_jsonl_data, mock_httpx_response):
        """Test get_scores_1m method with JSONL format."""
        mock_httpx_response.text = sample_jsonl_data

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_httpx_response

            client = OrbAPIClient(host="192.168.1.100")
            result = await client.get_scores_1m(format="jsonl")

            assert result == sample_jsonl_data
            call_args = mock_client.get.call_args
            assert "scores_1m.jsonl" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_responsiveness_1m(
        self, sample_responsiveness_data, mock_httpx_response
    ):
        """Test get_responsiveness method with 1m granularity."""
        mock_httpx_response.json.return_value = sample_responsiveness_data

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_httpx_response

            client = OrbAPIClient(host="192.168.1.100")
            result = await client.get_responsiveness(granularity="1m")

            assert result == sample_responsiveness_data
            call_args = mock_client.get.call_args
            assert "responsiveness_1m.json" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_responsiveness_1s(
        self, sample_responsiveness_data, mock_httpx_response
    ):
        """Test get_responsiveness method with 1s granularity."""
        mock_httpx_response.json.return_value = sample_responsiveness_data

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_httpx_response

            client = OrbAPIClient(host="192.168.1.100")
            result = await client.get_responsiveness(granularity="1s")

            assert result == sample_responsiveness_data
            call_args = mock_client.get.call_args
            assert "responsiveness_1s.json" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_responsiveness_15s(
        self, sample_responsiveness_data, mock_httpx_response
    ):
        """Test get_responsiveness method with 15s granularity."""
        mock_httpx_response.json.return_value = sample_responsiveness_data

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_httpx_response

            client = OrbAPIClient(host="192.168.1.100")
            result = await client.get_responsiveness(granularity="15s")

            assert result == sample_responsiveness_data
            call_args = mock_client.get.call_args
            assert "responsiveness_15s.json" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_web_responsiveness(
        self, sample_web_responsiveness_data, mock_httpx_response
    ):
        """Test get_web_responsiveness method."""
        mock_httpx_response.json.return_value = sample_web_responsiveness_data

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_httpx_response

            client = OrbAPIClient(host="192.168.1.100")
            result = await client.get_web_responsiveness()

            assert result == sample_web_responsiveness_data
            call_args = mock_client.get.call_args
            assert "web_responsiveness_results.json" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_speed_results(self, sample_speed_data, mock_httpx_response):
        """Test get_speed_results method."""
        mock_httpx_response.json.return_value = sample_speed_data

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_httpx_response

            client = OrbAPIClient(host="192.168.1.100")
            result = await client.get_speed_results()

            assert result == sample_speed_data
            call_args = mock_client.get.call_args
            assert "speed_results.json" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_all_datasets_basic(self, sample_all_datasets_response):
        """Test get_all_datasets method with basic configuration."""
        with (
            patch.object(
                OrbAPIClient,
                "get_scores_1m",
                return_value=sample_all_datasets_response["scores_1m"],
            ),
            patch.object(
                OrbAPIClient,
                "get_responsiveness",
                return_value=sample_all_datasets_response["responsiveness_1m"],
            ),
            patch.object(
                OrbAPIClient,
                "get_web_responsiveness",
                return_value=sample_all_datasets_response["web_responsiveness"],
            ),
            patch.object(
                OrbAPIClient,
                "get_speed_results",
                return_value=sample_all_datasets_response["speed_results"],
            ),
        ):
            client = OrbAPIClient(host="192.168.1.100")
            result = await client.get_all_datasets()

            assert "scores_1m" in result
            assert "responsiveness_1m" in result
            assert "web_responsiveness" in result
            assert "speed_results" in result
            assert result["scores_1m"] == sample_all_datasets_response["scores_1m"]

    @pytest.mark.asyncio
    async def test_get_all_datasets_with_all_responsiveness(
        self, sample_all_datasets_response
    ):
        """Test get_all_datasets method with all responsiveness granularities."""
        with (
            patch.object(
                OrbAPIClient,
                "get_scores_1m",
                return_value=sample_all_datasets_response["scores_1m"],
            ),
            patch.object(
                OrbAPIClient,
                "get_responsiveness",
                return_value=sample_all_datasets_response["responsiveness_1m"],
            ),
            patch.object(
                OrbAPIClient,
                "get_web_responsiveness",
                return_value=sample_all_datasets_response["web_responsiveness"],
            ),
            patch.object(
                OrbAPIClient,
                "get_speed_results",
                return_value=sample_all_datasets_response["speed_results"],
            ),
        ):
            client = OrbAPIClient(host="192.168.1.100")
            result = await client.get_all_datasets(include_all_responsiveness=True)

            assert "scores_1m" in result
            assert "responsiveness_1m" in result
            assert "responsiveness_15s" in result
            assert "responsiveness_1s" in result
            assert "web_responsiveness" in result
            assert "speed_results" in result

    @pytest.mark.asyncio
    async def test_get_all_datasets_with_error(
        self, sample_all_datasets_response, sample_error_response
    ):
        """Test get_all_datasets method with one dataset failing."""
        with (
            patch.object(
                OrbAPIClient,
                "get_scores_1m",
                return_value=sample_all_datasets_response["scores_1m"],
            ),
            patch.object(
                OrbAPIClient,
                "get_responsiveness",
                side_effect=Exception("Connection error"),
            ),
            patch.object(
                OrbAPIClient,
                "get_web_responsiveness",
                return_value=sample_all_datasets_response["web_responsiveness"],
            ),
            patch.object(
                OrbAPIClient,
                "get_speed_results",
                return_value=sample_all_datasets_response["speed_results"],
            ),
        ):
            client = OrbAPIClient(host="192.168.1.100")
            result = await client.get_all_datasets()

            assert "scores_1m" in result
            assert "responsiveness_1m" in result
            assert "error" in result["responsiveness_1m"]
            assert result["responsiveness_1m"]["error"] == "Connection error"
            assert "web_responsiveness" in result
            assert "speed_results" in result

    @pytest.mark.asyncio
    async def test_poll_dataset_success(self, sample_scores_data, mock_httpx_response):
        """Test poll_dataset method with successful polling."""
        mock_httpx_response.json.return_value = sample_scores_data

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_httpx_response

            client = OrbAPIClient(host="192.168.1.100")

            # Test with max_iterations=2
            results = []
            async for records in client.poll_dataset(
                "scores_1m", interval=0.01, max_iterations=2
            ):
                results.append(records)

            assert len(results) == 2
            assert all(result == sample_scores_data for result in results)

    @pytest.mark.asyncio
    async def test_poll_dataset_with_callback(
        self, sample_scores_data, mock_httpx_response
    ):
        """Test poll_dataset method with callback function."""
        mock_httpx_response.json.return_value = sample_scores_data
        callback_calls = []

        def test_callback(dataset_name, records):
            callback_calls.append((dataset_name, records))

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_httpx_response

            client = OrbAPIClient(host="192.168.1.100")

            # Test with max_iterations=1
            results = []
            async for records in client.poll_dataset(
                "scores_1m", interval=0.01, max_iterations=1, callback=test_callback
            ):
                results.append(records)

            assert len(results) == 1
            assert len(callback_calls) == 1
            assert callback_calls[0][0] == "scores_1m"
            assert callback_calls[0][1] == sample_scores_data

    @pytest.mark.asyncio
    async def test_poll_dataset_with_async_callback(
        self, sample_scores_data, mock_httpx_response
    ):
        """Test poll_dataset method with async callback function."""
        mock_httpx_response.json.return_value = sample_scores_data
        callback_calls = []

        async def test_async_callback(dataset_name, records):
            callback_calls.append((dataset_name, records))

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_httpx_response

            client = OrbAPIClient(host="192.168.1.100")

            # Test with max_iterations=1
            results = []
            async for records in client.poll_dataset(
                "scores_1m",
                interval=0.01,
                max_iterations=1,
                callback=test_async_callback,
            ):
                results.append(records)

            assert len(results) == 1
            assert len(callback_calls) == 1
            assert callback_calls[0][0] == "scores_1m"
            assert callback_calls[0][1] == sample_scores_data

    @pytest.mark.asyncio
    async def test_poll_dataset_with_error(self, mock_httpx_response):
        """Test poll_dataset method with HTTP error."""
        mock_httpx_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500 Internal Server Error",
            request=MagicMock(),
            response=mock_httpx_response,
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_httpx_response

            client = OrbAPIClient(host="192.168.1.100")

            # Test with max_iterations=1 - should handle error gracefully
            results = []
            async for records in client.poll_dataset(
                "scores_1m", interval=0.01, max_iterations=1
            ):
                results.append(records)

            # When an error occurs, the generator doesn't yield anything
            # The error is printed but no results are yielded
            assert len(results) == 0

    @pytest.mark.asyncio
    async def test_poll_dataset_infinite(self, sample_scores_data, mock_httpx_response):
        """Test poll_dataset method with infinite polling (max_iterations=None)."""
        mock_httpx_response.json.return_value = sample_scores_data

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_httpx_response

            client = OrbAPIClient(host="192.168.1.100")

            # Test with max_iterations=None and short interval
            # We'll manually break after a few iterations
            results = []
            count = 0
            async for records in client.poll_dataset(
                "scores_1m", interval=0.01, max_iterations=None
            ):
                results.append(records)
                count += 1
                if count >= 3:  # Break after 3 iterations
                    break

            assert len(results) == 3
            assert all(result == sample_scores_data for result in results)
