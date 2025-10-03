"""
Integration tests for orbnet package.

These tests verify that the components work together correctly,
but may require actual network connectivity or external services.
"""

import pytest
from unittest.mock import patch

from orbnet.client import OrbAPIClient
from orbnet.mcp_server import _get_client_info_impl


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
            OrbClientConfig,
            DatasetRequestParams,
            ResponsivenessRequestParams,
            AllDatasetsRequestParams,
        )

        # Test configuration chain
        config = OrbClientConfig(
            host="test-host", port=8080, caller_id="test-caller", timeout=30.0
        )

        # Test dataset request with config values
        dataset_params = DatasetRequestParams(format="json", caller_id=config.caller_id)

        # Test responsiveness request
        resp_params = ResponsivenessRequestParams(
            granularity="1s", format="jsonl", caller_id=config.caller_id
        )

        # Test all datasets request
        all_params = AllDatasetsRequestParams(
            format="json", caller_id=config.caller_id, include_all_responsiveness=True
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
            format="json",
            callback=test_callback,
            max_iterations=5,
        )

        client = OrbAPIClient(host="192.168.1.100")

        # Test that polling config can be used with client
        assert config.dataset_name == "scores_1m"
        assert config.interval == 10.0
        assert config.format == "json"
        assert config.callback == test_callback
        assert config.max_iterations == 5

    def test_error_handling_integration(self):
        """Test error handling across components."""
        from orbnet.models import OrbClientConfig
        from pydantic import ValidationError

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

    def test_import_integration(self):
        """Test that all modules can be imported together."""
        # Test that all main modules can be imported
        import orbnet
        import orbnet.client
        import orbnet.models
        import orbnet.mcp_server

        # Test that main classes are available
        from orbnet.client import OrbAPIClient
        from orbnet.models import OrbClientConfig
        from orbnet.mcp_server import _get_client_info_impl

        # Test that they can be instantiated
        client = OrbAPIClient(host="192.168.1.100")
        config = OrbClientConfig(host="192.168.1.100")
        info = _get_client_info_impl(host="192.168.1.100")

        assert client is not None
        assert config is not None
        assert info is not None
