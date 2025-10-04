"""
Pytest configuration and shared fixtures for orbnet tests.
"""

from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def sample_scores_data() -> List[Dict[str, Any]]:
    """Sample scores dataset response data."""
    return [
        {
            "orb_id": "test-orb-123",
            "orb_name": "Test Orb",
            "device_name": "test-device",
            "timestamp": 1700000000000,
            "score_version": "1.0.0",
            "orb_version": "2.1.0",
            "orb_score": 85.5,
            "responsiveness_score": 90.0,
            "reliability_score": 80.0,
            "speed_score": 87.5,
            "speed_age_ms": 0,
            "lag_avg_us": 25000.0,
            "download_avg_kbps": 50000,
            "upload_avg_kbps": 10000,
            "unresponsive_ms": 0.0,
            "measured_ms": 60000.0,
            "lag_count": 60,
            "speed_count": 1,
            "network_type": 1,
            "network_state": 1,
            "country_code": "US",
            "city_name": "San Francisco",
            "isp_name": "Test ISP",
            "public_ip": "192.168.1.100",
            "latitude": 37.7749,
            "longitude": -122.4194,
            "location_source": 1,
        },
        {
            "orb_id": "test-orb-123",
            "orb_name": "Test Orb",
            "device_name": "test-device",
            "timestamp": 1700000060000,
            "score_version": "1.0.0",
            "orb_version": "2.1.0",
            "orb_score": 88.2,
            "responsiveness_score": 92.0,
            "reliability_score": 85.0,
            "speed_score": 88.0,
            "speed_age_ms": 0,
            "lag_avg_us": 22000.0,
            "download_avg_kbps": 52000,
            "upload_avg_kbps": 10500,
            "unresponsive_ms": 0.0,
            "measured_ms": 60000.0,
            "lag_count": 60,
            "speed_count": 1,
            "network_type": 1,
            "network_state": 1,
            "country_code": "US",
            "city_name": "San Francisco",
            "isp_name": "Test ISP",
            "public_ip": "192.168.1.100",
            "latitude": 37.7749,
            "longitude": -122.4194,
            "location_source": 1,
        },
    ]


@pytest.fixture
def sample_responsiveness_data() -> List[Dict[str, Any]]:
    """Sample responsiveness dataset response data."""
    return [
        {
            "orb_id": "test-orb-123",
            "orb_name": "Test Orb",
            "device_name": "test-device",
            "timestamp": 1700000000000,
            "orb_version": "2.1.0",
            "lag_avg_us": 25000,
            "latency_avg_us": 30000,
            "jitter_avg_us": 2000,
            "latency_count": 60.0,
            "latency_lost_count": 0,
            "packet_loss_pct": 0.0,
            "lag_count": 60,
            "router_lag_avg_us": 5000,
            "router_latency_avg_us": 8000,
            "router_jitter_avg_us": 500,
            "router_latency_count": 60.0,
            "router_latency_lost_count": 0,
            "router_packet_loss_pct": 0.0,
            "router_lag_count": 60,
            "network_type": 1,
            "network_state": 1,
            "country_code": "US",
            "city_name": "San Francisco",
            "isp_name": "Test ISP",
            "public_ip": "192.168.1.100",
            "latitude": 37.7749,
            "longitude": -122.4194,
            "location_source": 1,
            "network_name": "Test Network",
            "pingers": "test-pinger-1,test-pinger-2",
        }
    ]


@pytest.fixture
def sample_web_responsiveness_data() -> List[Dict[str, Any]]:
    """Sample web responsiveness dataset response data."""
    return [
        {
            "orb_id": "test-orb-123",
            "orb_name": "Test Orb",
            "device_name": "test-device",
            "timestamp": 1700000000000,
            "orb_version": "2.1.0",
            "ttfb_us": 150000,
            "dns_us": 50000,
            "network_type": 1,
            "network_state": 1,
            "country_code": "US",
            "city_name": "San Francisco",
            "isp_name": "Test ISP",
            "public_ip": "192.168.1.100",
            "latitude": 37.7749,
            "longitude": -122.4194,
            "location_source": 1,
            "network_name": "Test Network",
            "web_url": "https://example.com",
        }
    ]


@pytest.fixture
def sample_speed_data() -> List[Dict[str, Any]]:
    """Sample speed test dataset response data."""
    return [
        {
            "orb_id": "test-orb-123",
            "orb_name": "Test Orb",
            "device_name": "test-device",
            "timestamp": 1700000000000,
            "orb_version": "2.1.0",
            "download_kbps": 50000,
            "upload_kbps": 10000,
            "network_type": 1,
            "network_state": 1,
            "country_code": "US",
            "city_name": "San Francisco",
            "isp_name": "Test ISP",
            "public_ip": "192.168.1.100",
            "latitude": 37.7749,
            "longitude": -122.4194,
            "location_source": 1,
            "network_name": "Test Network",
            "speed_test_engine": "test-engine",
            "speed_test_server": "test-server-1",
        }
    ]




@pytest.fixture
def mock_httpx_response():
    """Mock httpx response object."""
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json = MagicMock()
    response.text = "mock response text"
    return response


@pytest.fixture
def mock_httpx_client():
    """Mock httpx AsyncClient."""
    client = AsyncMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    return client


@pytest.fixture
def mock_httpx_get(mock_httpx_client, mock_httpx_response):
    """Mock httpx.AsyncClient.get method."""
    mock_httpx_client.get = AsyncMock(return_value=mock_httpx_response)
    return mock_httpx_client.get


@pytest.fixture
def mock_httpx_client_context(mock_httpx_client):
    """Mock httpx.AsyncClient context manager."""
    with pytest.Mock() as mock_context:
        mock_context.return_value.__aenter__ = AsyncMock(return_value=mock_httpx_client)
        mock_context.return_value.__aexit__ = AsyncMock(return_value=None)
        return mock_context


@pytest.fixture
def sample_all_datasets_response(
    sample_scores_data,
    sample_responsiveness_data,
    sample_web_responsiveness_data,
    sample_speed_data,
):
    """Sample response for get_all_datasets."""
    return {
        "scores_1m": sample_scores_data,
        "responsiveness_1m": sample_responsiveness_data,
        "web_responsiveness": sample_web_responsiveness_data,
        "speed_results": sample_speed_data,
    }


@pytest.fixture
def sample_error_response():
    """Sample error response for failed dataset requests."""
    return {"error": "Connection timeout"}


@pytest.fixture
def default_client_config():
    """Default client configuration for testing."""
    return {
        "host": "localhost",
        "port": 7080,
        "caller_id": "test-caller-id",
        "client_id": "orbnet/0.1.0",
        "timeout": 30.0,
    }
