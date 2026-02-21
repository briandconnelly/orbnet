"""
Integration tests for orbnet package.

These tests verify that the components work together correctly,
but may require actual network connectivity or external services.
"""

import pytest

from orbnet.client import OrbAPIClient
from orbnet.mcp_server import _get_client_info_impl
from orbnet.models import WifiLinkRecord


class TestIntegration:
    """Integration tests for orbnet components."""

    def test_client_configuration_integration(self):
        """Test that client configuration works end-to-end."""
        client = OrbAPIClient(
            host="test-host",
            port=8080,
            caller_id="integration-test",
            client_id="integration-client",
            timeout=60.0,
        )

        assert client.host == "test-host"
        assert client.port == 8080
        assert client.caller_id == "integration-test"
        assert client.client_id == "integration-client"
        assert client.timeout == 60.0
        assert client.base_url == "http://test-host:8080"

    def test_mcp_server_client_creation(self):
        """Test that MCP server creates clients correctly."""
        info = _get_client_info_impl(
            host="test-host", port=8080, caller_id="mcp-test", timeout=45.0
        )

        assert info["host"] == "test-host"
        assert info["port"] == 8080
        assert info["caller_id"] == "mcp-test"
        assert info["timeout"] == 45.0
        assert info["base_url"] == "http://test-host:8080"

    @pytest.mark.asyncio
    async def test_client_headers_integration(self):
        """Test that client headers are properly constructed."""
        client = OrbAPIClient(host="192.168.1.100", client_id="test-client")
        headers = client._get_headers()

        expected_headers = {"Accept": "application/json", "User-Agent": "test-client"}
        assert headers == expected_headers

    def test_model_validation_integration(self):
        """Test that models work together in realistic scenarios."""
        from orbnet.models import (
            AllDatasetsRequestParams,
            DatasetRequestParams,
            OrbClientConfig,
            ResponsivenessRequestParams,
        )

        # Test configuration chain
        config = OrbClientConfig(
            host="test-host", port=8080, caller_id="test-caller", timeout=30.0
        )

        # Test dataset request with config values
        dataset_params = DatasetRequestParams(caller_id=config.caller_id)

        # Test responsiveness request
        resp_params = ResponsivenessRequestParams(
            granularity="1s", caller_id=config.caller_id
        )

        # Test all datasets request
        all_params = AllDatasetsRequestParams(
            caller_id=config.caller_id, include_all_responsiveness=True
        )

        # Verify all parameters are valid
        assert dataset_params.caller_id == config.caller_id
        assert resp_params.caller_id == config.caller_id
        assert all_params.caller_id == config.caller_id
        assert all_params.include_all_responsiveness is True

    @pytest.mark.asyncio
    async def test_polling_configuration_integration(self):
        """Test that polling configuration works with client."""
        from orbnet.models import PollingConfig

        def test_callback(dataset_name, records):
            pass

        config = PollingConfig(
            dataset_name="scores_1m",
            interval=10.0,
            callback=test_callback,
            max_iterations=5,
        )

        OrbAPIClient(host="192.168.1.100")

        # Test that polling config can be used with client
        assert config.dataset_name == "scores_1m"
        assert config.interval == 10.0
        assert config.callback == test_callback
        assert config.max_iterations == 5

    def test_error_handling_integration(self):
        """Test error handling across components."""
        from pydantic import ValidationError

        from orbnet.models import OrbClientConfig

        # Test invalid configuration
        with pytest.raises(ValidationError):
            OrbClientConfig(port=0)  # Invalid port

        with pytest.raises(ValidationError):
            OrbClientConfig(timeout=-1.0)  # Invalid timeout

        # Test valid configuration
        config = OrbClientConfig(host="192.168.1.100", port=8080, timeout=30.0)
        assert config.host == "192.168.1.100"
        assert config.port == 8080
        assert config.timeout == 30.0

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_client_timeout_behavior(self):
        """Test client timeout behavior (marked as slow)."""
        # This test would require actual network calls with timeouts
        # For now, we'll just test the configuration
        client = OrbAPIClient(host="192.168.1.100", timeout=0.1)  # Very short timeout
        assert client.timeout == 0.1

        # In a real integration test, we would:
        # 1. Start a mock server that delays responses
        # 2. Test that the client times out appropriately
        # 3. Verify error handling

    def test_wifi_link_record_model_integration(self, sample_wifi_link_data):
        """Test WifiLinkRecord model validates identifiers, measures, and dimensions."""
        record = WifiLinkRecord(**sample_wifi_link_data[0])

        # Identifiers
        assert record.orb_id == "test-orb-123"
        assert record.orb_name == "Test Orb"
        assert record.device_name == "test-device"
        assert record.timestamp == 1700000000000
        assert record.orb_version == "2.1.0"

        # Measures
        assert record.rssi_avg == -55.0
        assert record.rssi_count == 60
        assert record.snr_avg == 40.0
        assert record.noise_avg == -95.0
        assert record.tx_rate_mbps == 300.0
        assert record.rx_rate_mbps == 270.0
        assert record.phy_mode == "802.11ac"
        assert record.channel_number == 36
        assert record.channel_band == "5 GHz"
        assert record.frequency_mhz == 5180

        # Dimensions
        assert record.bssid == "aa:bb:cc:dd:ee:ff"
        assert record.network_name == "Test Network"
        assert record.network_type == 1

    def test_wifi_link_record_optional_fields_integration(self):
        """Test WifiLinkRecord with minimal data; optional fields default to None."""
        minimal_data = {
            "orb_id": "test-orb-123",
            "orb_name": "Test Orb",
            "device_name": "test-device",
            "timestamp": 1700000000000,
            "orb_version": "2.1.0",
            "rssi_avg": -60.0,
            "rssi_count": 60,
            "tx_rate_mbps": 200.0,
            "tx_rate_count": 60,
            "rx_rate_count": 60,
            "snr_avg": 30.0,
            "snr_count": 60,
            "noise_avg": -90.0,
            "noise_count": 60,
            "phy_mode": "802.11ac",
            "channel_number": 6,
            "channel_band": "2.4 GHz",
            "network_type": 1,
        }
        record = WifiLinkRecord(**minimal_data)

        # Platform-specific optional fields default to None
        assert record.rx_rate_mbps is None
        assert record.mcs is None
        assert record.nss is None
        assert record.security is None
        assert record.channel_width is None
        assert record.frequency_mhz is None
        assert record.bssid is None
        assert record.network_name is None

    def test_wifi_link_record_model_dump_integration(self, sample_wifi_link_data):
        """Test WifiLinkRecord round-trips correctly via model_dump()."""
        record = WifiLinkRecord(**sample_wifi_link_data[0])
        dumped = record.model_dump()

        assert dumped["rssi_avg"] == sample_wifi_link_data[0]["rssi_avg"]
        assert dumped["snr_avg"] == sample_wifi_link_data[0]["snr_avg"]
        assert dumped["tx_rate_mbps"] == sample_wifi_link_data[0]["tx_rate_mbps"]
        assert dumped["channel_band"] == sample_wifi_link_data[0]["channel_band"]
        assert dumped["phy_mode"] == sample_wifi_link_data[0]["phy_mode"]
        assert dumped["timestamp"] == sample_wifi_link_data[0]["timestamp"]

    def test_wifi_link_record_extra_fields_integration(self, sample_wifi_link_data):
        """Test WifiLinkRecord accepts extra fields and exposes them via model_extra."""
        data = {**sample_wifi_link_data[0], "unknown_field": "some_value"}
        record = WifiLinkRecord(**data)

        assert record.model_extra is not None
        assert "unknown_field" in record.model_extra
        assert record.model_extra["unknown_field"] == "some_value"

    def test_import_integration(self):
        """Test that all modules can be imported together."""
        # Test that all main modules can be imported

        # Test that main classes are available
        from orbnet.client import OrbAPIClient
        from orbnet.mcp_server import _get_client_info_impl
        from orbnet.models import (
            AllDatasetsResponse,
            OrbClientConfig,
            ResponsivenessRecord,
            ScoreRecord,
            SpeedRecord,
            WebResponsivenessRecord,
            WifiLinkRecord,
        )

        # Test that they can be instantiated
        client = OrbAPIClient(host="192.168.1.100")
        config = OrbClientConfig(host="192.168.1.100")
        info = _get_client_info_impl(host="192.168.1.100")

        assert client is not None
        assert config is not None
        assert info is not None

        # Verify record types are available
        assert ScoreRecord is not None
        assert ResponsivenessRecord is not None
        assert WebResponsivenessRecord is not None
        assert SpeedRecord is not None
        assert AllDatasetsResponse is not None
        assert WifiLinkRecord is not None
