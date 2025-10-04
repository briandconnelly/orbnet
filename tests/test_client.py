"""
Tests for OrbAPIClient in orbnet.client.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from orbnet.client import OrbAPIClient
from orbnet.models import (
    AllDatasetsResponse,
    ResponsivenessRecord,
    ScoreRecord,
    SpeedRecord,
    WebResponsivenessRecord,
)


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
    async def test_get_dataset(self, sample_scores_data, mock_httpx_response):
        """Test _get_dataset method."""
        mock_httpx_response.json.return_value = sample_scores_data

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_httpx_response

            client = OrbAPIClient(host="192.168.1.100")
            result = await client._get_dataset("scores_1m")

            assert result == sample_scores_data
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert "scores_1m.json" in call_args[0][0]
            assert call_args[1]["params"]["id"] == client.caller_id

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
            result = await client._get_dataset("scores_1m", caller_id="custom-caller")

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
                await client._get_dataset("scores_1m")

    @pytest.mark.asyncio
    async def test_get_scores_1m(self, sample_scores_data, mock_httpx_response):
        """Test get_scores_1m method returns ScoreRecord objects."""
        mock_httpx_response.json.return_value = sample_scores_data

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_httpx_response

            client = OrbAPIClient(host="192.168.1.100")
            result = await client.get_scores_1m()

            # Check result is a list of ScoreRecord objects
            assert isinstance(result, list)
            assert len(result) == len(sample_scores_data)
            assert all(isinstance(r, ScoreRecord) for r in result)

            # Check data integrity
            assert result[0].orb_id == sample_scores_data[0]["orb_id"]
            assert result[0].orb_score == sample_scores_data[0]["orb_score"]
            assert result[0].isp_name == sample_scores_data[0]["isp_name"]

            call_args = mock_client.get.call_args
            assert "scores_1m.json" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_responsiveness_1m(
        self, sample_responsiveness_data, mock_httpx_response
    ):
        """Test get_responsiveness method with 1m granularity returns ResponsivenessRecord objects."""
        mock_httpx_response.json.return_value = sample_responsiveness_data

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_httpx_response

            client = OrbAPIClient(host="192.168.1.100")
            result = await client.get_responsiveness(granularity="1m")

            # Check result is a list of ResponsivenessRecord objects
            assert isinstance(result, list)
            assert len(result) == len(sample_responsiveness_data)
            assert all(isinstance(r, ResponsivenessRecord) for r in result)

            # Check data integrity
            assert result[0].orb_id == sample_responsiveness_data[0]["orb_id"]
            assert result[0].lag_avg_us == sample_responsiveness_data[0]["lag_avg_us"]
            assert (
                result[0].packet_loss_pct
                == sample_responsiveness_data[0]["packet_loss_pct"]
            )

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

            assert isinstance(result, list)
            assert all(isinstance(r, ResponsivenessRecord) for r in result)
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

            assert isinstance(result, list)
            assert all(isinstance(r, ResponsivenessRecord) for r in result)
            call_args = mock_client.get.call_args
            assert "responsiveness_15s.json" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_web_responsiveness(
        self, sample_web_responsiveness_data, mock_httpx_response
    ):
        """Test get_web_responsiveness method returns WebResponsivenessRecord objects."""
        mock_httpx_response.json.return_value = sample_web_responsiveness_data

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_httpx_response

            client = OrbAPIClient(host="192.168.1.100")
            result = await client.get_web_responsiveness()

            # Check result is a list of WebResponsivenessRecord objects
            assert isinstance(result, list)
            assert len(result) == len(sample_web_responsiveness_data)
            assert all(isinstance(r, WebResponsivenessRecord) for r in result)

            # Check data integrity
            assert result[0].orb_id == sample_web_responsiveness_data[0]["orb_id"]
            assert result[0].ttfb_us == sample_web_responsiveness_data[0]["ttfb_us"]
            assert result[0].web_url == sample_web_responsiveness_data[0]["web_url"]

            call_args = mock_client.get.call_args
            assert "web_responsiveness_results.json" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_speed_results(self, sample_speed_data, mock_httpx_response):
        """Test get_speed_results method returns SpeedRecord objects."""
        mock_httpx_response.json.return_value = sample_speed_data

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_httpx_response

            client = OrbAPIClient(host="192.168.1.100")
            result = await client.get_speed_results()

            # Check result is a list of SpeedRecord objects
            assert isinstance(result, list)
            assert len(result) == len(sample_speed_data)
            assert all(isinstance(r, SpeedRecord) for r in result)

            # Check data integrity
            assert result[0].orb_id == sample_speed_data[0]["orb_id"]
            assert result[0].download_kbps == sample_speed_data[0]["download_kbps"]
            assert (
                result[0].speed_test_server == sample_speed_data[0]["speed_test_server"]
            )

            call_args = mock_client.get.call_args
            assert "speed_results.json" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_all_datasets_basic(
        self,
        sample_scores_data,
        sample_responsiveness_data,
        sample_web_responsiveness_data,
        sample_speed_data,
    ):
        """Test get_all_datasets method returns AllDatasetsResponse."""
        with (
            patch.object(
                OrbAPIClient,
                "get_scores_1m",
                return_value=[ScoreRecord(**r) for r in sample_scores_data],
            ),
            patch.object(
                OrbAPIClient,
                "get_responsiveness",
                return_value=[
                    ResponsivenessRecord(**r) for r in sample_responsiveness_data
                ],
            ),
            patch.object(
                OrbAPIClient,
                "get_web_responsiveness",
                return_value=[
                    WebResponsivenessRecord(**r) for r in sample_web_responsiveness_data
                ],
            ),
            patch.object(
                OrbAPIClient,
                "get_speed_results",
                return_value=[SpeedRecord(**r) for r in sample_speed_data],
            ),
        ):
            client = OrbAPIClient(host="192.168.1.100")
            result = await client.get_all_datasets()

            # Check result is AllDatasetsResponse
            assert isinstance(result, AllDatasetsResponse)

            # Check all required datasets are present
            assert isinstance(result.scores_1m, list)
            assert isinstance(result.responsiveness_1m, list)
            assert isinstance(result.web_responsiveness, list)
            assert isinstance(result.speed_results, list)

            # Check data types
            assert all(isinstance(r, ScoreRecord) for r in result.scores_1m)
            assert all(
                isinstance(r, ResponsivenessRecord) for r in result.responsiveness_1m
            )
            assert all(
                isinstance(r, WebResponsivenessRecord)
                for r in result.web_responsiveness
            )
            assert all(isinstance(r, SpeedRecord) for r in result.speed_results)

    @pytest.mark.asyncio
    async def test_get_all_datasets_with_all_responsiveness(
        self,
        sample_scores_data,
        sample_responsiveness_data,
        sample_web_responsiveness_data,
        sample_speed_data,
    ):
        """Test get_all_datasets method with all responsiveness granularities."""
        with (
            patch.object(
                OrbAPIClient,
                "get_scores_1m",
                return_value=[ScoreRecord(**r) for r in sample_scores_data],
            ),
            patch.object(
                OrbAPIClient,
                "get_responsiveness",
                return_value=[
                    ResponsivenessRecord(**r) for r in sample_responsiveness_data
                ],
            ),
            patch.object(
                OrbAPIClient,
                "get_web_responsiveness",
                return_value=[
                    WebResponsivenessRecord(**r) for r in sample_web_responsiveness_data
                ],
            ),
            patch.object(
                OrbAPIClient,
                "get_speed_results",
                return_value=[SpeedRecord(**r) for r in sample_speed_data],
            ),
        ):
            client = OrbAPIClient(host="192.168.1.100")
            result = await client.get_all_datasets(include_all_responsiveness=True)

            assert isinstance(result, AllDatasetsResponse)
            assert isinstance(result.scores_1m, list)
            assert isinstance(result.responsiveness_1m, list)
            assert isinstance(result.responsiveness_15s, list)
            assert isinstance(result.responsiveness_1s, list)
            assert isinstance(result.web_responsiveness, list)
            assert isinstance(result.speed_results, list)

    @pytest.mark.asyncio
    async def test_get_all_datasets_with_error(
        self,
        sample_scores_data,
        sample_web_responsiveness_data,
        sample_speed_data,
    ):
        """Test get_all_datasets method with one dataset failing."""
        with (
            patch.object(
                OrbAPIClient,
                "get_scores_1m",
                return_value=[ScoreRecord(**r) for r in sample_scores_data],
            ),
            patch.object(
                OrbAPIClient,
                "get_responsiveness",
                side_effect=Exception("Connection error"),
            ),
            patch.object(
                OrbAPIClient,
                "get_web_responsiveness",
                return_value=[
                    WebResponsivenessRecord(**r) for r in sample_web_responsiveness_data
                ],
            ),
            patch.object(
                OrbAPIClient,
                "get_speed_results",
                return_value=[SpeedRecord(**r) for r in sample_speed_data],
            ),
        ):
            client = OrbAPIClient(host="192.168.1.100")
            result = await client.get_all_datasets()

            assert isinstance(result, AllDatasetsResponse)
            assert isinstance(result.scores_1m, list)
            assert isinstance(result.responsiveness_1m, dict)
            assert "error" in result.responsiveness_1m
            assert result.responsiveness_1m["error"] == "Connection error"
            assert isinstance(result.web_responsiveness, list)
            assert isinstance(result.speed_results, list)

    @pytest.mark.asyncio
    async def test_poll_dataset_success(self, sample_scores_data, mock_httpx_response):
        """Test poll_dataset method with successful polling returns Pydantic objects."""
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
            # Check all results are lists of ScoreRecord objects
            assert all(isinstance(r, list) for r in results)
            assert all(isinstance(rec, ScoreRecord) for r in results for rec in r)

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
            # Check callback received Pydantic objects
            assert all(isinstance(r, ScoreRecord) for r in callback_calls[0][1])

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
            # Check callback received Pydantic objects
            assert all(isinstance(r, ScoreRecord) for r in callback_calls[0][1])

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
    async def test_poll_dataset_invalid_dataset_name(self):
        """Test poll_dataset method with invalid dataset name."""
        client = OrbAPIClient(host="192.168.1.100")

        with pytest.raises(ValueError, match="Unknown dataset"):
            async for _ in client.poll_dataset(
                "invalid_dataset", interval=0.01, max_iterations=1
            ):
                pass

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
            assert all(isinstance(r, list) for r in results)
            assert all(isinstance(rec, ScoreRecord) for r in results for rec in r)
