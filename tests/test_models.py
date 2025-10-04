"""
Tests for Pydantic models in orbnet.models.
"""

import pytest
from pydantic import ValidationError

from orbnet.models import (
    AllDatasetsRequestParams,
    DatasetRequestParams,
    NetworkDimensions,
    OrbClientConfig,
    PollingConfig,
    ResponsivenessMeasures,
    ResponsivenessRequestParams,
    ScoreIdentifiers,
    ScoreMeasures,
    SpeedMeasures,
    WebResponsivenessMeasures,
)


class TestOrbClientConfig:
    """Test OrbClientConfig model."""

    def test_default_values(self):
        """Test default configuration values."""
        config = OrbClientConfig(host="192.168.1.100")
        assert config.host == "192.168.1.100"
        assert config.port == 7080
        assert config.caller_id is None
        assert config.client_id is None
        assert config.timeout == 30.0

    def test_custom_values(self):
        """Test custom configuration values."""
        config = OrbClientConfig(
            host="192.168.1.100",
            port=8080,
            caller_id="test-caller",
            client_id="test-client",
            timeout=60.0,
        )
        assert config.host == "192.168.1.100"
        assert config.port == 8080
        assert config.caller_id == "test-caller"
        assert config.client_id == "test-client"
        assert config.timeout == 60.0

    def test_port_validation(self):
        """Test port number validation."""
        # Valid ports
        OrbClientConfig(host="192.168.1.100", port=1)
        OrbClientConfig(host="192.168.1.100", port=65535)

        # Invalid ports
        with pytest.raises(ValidationError):
            OrbClientConfig(host="192.168.1.100", port=0)
        with pytest.raises(ValidationError):
            OrbClientConfig(host="192.168.1.100", port=65536)

    def test_timeout_validation(self):
        """Test timeout validation."""
        # Valid timeout
        OrbClientConfig(host="192.168.1.100", timeout=0.1)

        # Invalid timeout
        with pytest.raises(ValidationError):
            OrbClientConfig(host="192.168.1.100", timeout=0)
        with pytest.raises(ValidationError):
            OrbClientConfig(host="192.168.1.100", timeout=-1.0)


class TestDatasetRequestParams:
    """Test DatasetRequestParams model."""

    def test_default_values(self):
        """Test default parameter values."""
        params = DatasetRequestParams()
        assert params.caller_id is None

    def test_custom_values(self):
        """Test custom parameter values."""
        params = DatasetRequestParams(
            caller_id="test-caller", extra_param="extra_value"
        )
        assert params.caller_id == "test-caller"
        assert params.extra_param == "extra_value"



class TestResponsivenessRequestParams:
    """Test ResponsivenessRequestParams model."""

    def test_default_values(self):
        """Test default parameter values."""
        params = ResponsivenessRequestParams()
        assert params.caller_id is None
        assert params.granularity == "1m"

    def test_custom_values(self):
        """Test custom parameter values."""
        params = ResponsivenessRequestParams(
            caller_id="test-caller", granularity="1s"
        )
        assert params.caller_id == "test-caller"
        assert params.granularity == "1s"

    def test_granularity_validation(self):
        """Test granularity validation."""
        # Valid granularities
        ResponsivenessRequestParams(granularity="1s")
        ResponsivenessRequestParams(granularity="15s")
        ResponsivenessRequestParams(granularity="1m")

        # Invalid granularity
        with pytest.raises(ValidationError):
            ResponsivenessRequestParams(granularity="5m")


class TestAllDatasetsRequestParams:
    """Test AllDatasetsRequestParams model."""

    def test_default_values(self):
        """Test default parameter values."""
        params = AllDatasetsRequestParams()
        assert params.caller_id is None
        assert params.include_all_responsiveness is False

    def test_custom_values(self):
        """Test custom parameter values."""
        params = AllDatasetsRequestParams(
            caller_id="test-caller", include_all_responsiveness=True
        )
        assert params.caller_id == "test-caller"
        assert params.include_all_responsiveness is True


class TestPollingConfig:
    """Test PollingConfig model."""

    def test_required_fields(self):
        """Test required fields."""
        config = PollingConfig(dataset_name="scores_1m")
        assert config.dataset_name == "scores_1m"
        assert config.interval == 60.0
        assert config.callback is None
        assert config.max_iterations is None

    def test_custom_values(self):
        """Test custom configuration values."""

        def dummy_callback(dataset_name, records):
            pass

        config = PollingConfig(
            dataset_name="responsiveness_1s",
            interval=10.0,
            callback=dummy_callback,
            max_iterations=5,
        )
        assert config.dataset_name == "responsiveness_1s"
        assert config.interval == 10.0
        assert config.callback == dummy_callback
        assert config.max_iterations == 5

    def test_interval_validation(self):
        """Test interval validation."""
        # Valid interval
        PollingConfig(dataset_name="test", interval=0.1)

        # Invalid interval
        with pytest.raises(ValidationError):
            PollingConfig(dataset_name="test", interval=0)
        with pytest.raises(ValidationError):
            PollingConfig(dataset_name="test", interval=-1.0)

    def test_max_iterations_validation(self):
        """Test max_iterations validation."""
        # Valid max_iterations
        PollingConfig(dataset_name="test", max_iterations=1)
        PollingConfig(dataset_name="test", max_iterations=None)

        # Invalid max_iterations
        with pytest.raises(ValidationError):
            PollingConfig(dataset_name="test", max_iterations=0)


class TestScoreIdentifiers:
    """Test ScoreIdentifiers model."""

    def test_valid_data(self):
        """Test valid score identifiers data."""
        data = {
            "orb_id": "test-orb-123",
            "orb_name": "Test Orb",
            "device_name": "test-device",
            "timestamp": 1700000000000,
            "score_version": "1.0.0",
            "orb_version": "2.1.0",
        }
        identifiers = ScoreIdentifiers(**data)
        assert identifiers.orb_id == "test-orb-123"
        assert identifiers.orb_name == "Test Orb"
        assert identifiers.device_name == "test-device"
        assert identifiers.timestamp == 1700000000000
        assert identifiers.score_version == "1.0.0"
        assert identifiers.orb_version == "2.1.0"

    def test_missing_required_fields(self):
        """Test missing required fields."""
        with pytest.raises(ValidationError):
            ScoreIdentifiers(orb_id="test-orb-123")


class TestScoreMeasures:
    """Test ScoreMeasures model."""

    def test_valid_data(self):
        """Test valid score measures data."""
        data = {
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
        }
        measures = ScoreMeasures(**data)
        assert measures.orb_score == 85.5
        assert measures.responsiveness_score == 90.0
        assert measures.reliability_score == 80.0
        assert measures.speed_score == 87.5
        assert measures.speed_age_ms == 0
        assert measures.lag_avg_us == 25000.0
        assert measures.download_avg_kbps == 50000
        assert measures.upload_avg_kbps == 10000
        assert measures.unresponsive_ms == 0.0
        assert measures.measured_ms == 60000.0
        assert measures.lag_count == 60
        assert measures.speed_count == 1


class TestNetworkDimensions:
    """Test NetworkDimensions model."""

    def test_valid_data(self):
        """Test valid network dimensions data."""
        data = {
            "network_type": 1,
            "network_state": 1,
            "country_code": "US",
            "city_name": "San Francisco",
            "isp_name": "Test ISP",
            "public_ip": "192.168.1.100",
            "latitude": 37.7749,
            "longitude": -122.4194,
            "location_source": 1,
        }
        dimensions = NetworkDimensions(**data)
        assert dimensions.network_type == 1
        assert dimensions.network_state == 1
        assert dimensions.country_code == "US"
        assert dimensions.city_name == "San Francisco"
        assert dimensions.isp_name == "Test ISP"
        assert dimensions.public_ip == "192.168.1.100"
        assert dimensions.latitude == 37.7749
        assert dimensions.longitude == -122.4194
        assert dimensions.location_source == 1


class TestResponsivenessMeasures:
    """Test ResponsivenessMeasures model."""

    def test_valid_data(self):
        """Test valid responsiveness measures data."""
        data = {
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
        }
        measures = ResponsivenessMeasures(**data)
        assert measures.lag_avg_us == 25000
        assert measures.latency_avg_us == 30000
        assert measures.jitter_avg_us == 2000
        assert measures.latency_count == 60.0
        assert measures.latency_lost_count == 0
        assert measures.packet_loss_pct == 0.0
        assert measures.lag_count == 60
        assert measures.router_lag_avg_us == 5000
        assert measures.router_latency_avg_us == 8000
        assert measures.router_jitter_avg_us == 500
        assert measures.router_latency_count == 60.0
        assert measures.router_latency_lost_count == 0
        assert measures.router_packet_loss_pct == 0.0
        assert measures.router_lag_count == 60


class TestWebResponsivenessMeasures:
    """Test WebResponsivenessMeasures model."""

    def test_valid_data(self):
        """Test valid web responsiveness measures data."""
        data = {
            "ttfb_us": 150000,
            "dns_us": 50000,
        }
        measures = WebResponsivenessMeasures(**data)
        assert measures.ttfb_us == 150000
        assert measures.dns_us == 50000


class TestSpeedMeasures:
    """Test SpeedMeasures model."""

    def test_valid_data(self):
        """Test valid speed measures data."""
        data = {
            "download_kbps": 50000,
            "upload_kbps": 10000,
        }
        measures = SpeedMeasures(**data)
        assert measures.download_kbps == 50000
        assert measures.upload_kbps == 10000
