"""
Tests for Pydantic models in orbnet.models.
"""

import pytest
from pydantic import ValidationError

from orbnet.models import (
    AllDatasetsResponse,
    NetworkDimensions,
    PollingConfig,
    ResponsivenessMeasures,
    ResponsivenessRecord,
    ScoreIdentifiers,
    ScoreMeasures,
    ScoreRecord,
    SpeedMeasures,
    SpeedRecord,
    WebResponsivenessMeasures,
    WebResponsivenessRecord,
    WifiLinkMeasures,
    WifiLinkRecord,
)


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

    def test_callback_accepts_sync_and_async(self):
        """The callback alias must accept sync and async callables alike."""

        def sync_cb(name, records):
            return None

        async def async_cb(name, records):
            return None

        PollingConfig(dataset_name="test", callback=sync_cb)
        PollingConfig(dataset_name="test", callback=async_cb)


def test_polling_callback_type_alias_is_exported():
    """PollingCallback should be importable for users typing their own callbacks."""
    from orbnet.models import PollingCallback

    assert PollingCallback is not None


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

    def test_minimal_data_identifiable_false(self):
        """Test score identifiers with minimal data (identifiable=false scenario)."""
        data = {
            "orb_id": "test-orb-123",
            "timestamp": 1700000000000,
            "score_version": "1.0.0",
            "orb_version": "2.1.0",
        }
        identifiers = ScoreIdentifiers.model_validate(data)
        assert identifiers.orb_id == "test-orb-123"
        assert identifiers.orb_name is None
        assert identifiers.device_name is None
        assert identifiers.timestamp == 1700000000000

    def test_missing_required_fields(self):
        """Test missing required fields."""
        with pytest.raises(ValidationError):
            ScoreIdentifiers.model_validate({"orb_id": "test-orb-123"})


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
        assert dimensions.country_code == "US"
        assert dimensions.city_name == "San Francisco"
        assert dimensions.isp_name == "Test ISP"
        assert dimensions.public_ip == "192.168.1.100"
        assert dimensions.latitude == 37.7749
        assert dimensions.longitude == -122.4194
        assert dimensions.location_source == 1

    def test_minimal_data_identifiable_false(self):
        """Test network dimensions with minimal data (identifiable=false scenario)."""
        data = {
            "network_type": 1,
        }
        dimensions = NetworkDimensions.model_validate(data)
        assert dimensions.network_type == 1
        assert dimensions.country_code is None
        assert dimensions.city_name is None
        assert dimensions.isp_name is None
        assert dimensions.public_ip is None
        assert dimensions.latitude is None
        assert dimensions.longitude is None
        assert dimensions.location_source is None


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

    def test_optional_router_fields(self):
        """Test that router fields are optional (Orb omits them when unavailable)."""
        data = {
            "lag_avg_us": 25000,
            "latency_avg_us": 30000,
            "jitter_avg_us": 2000,
            "latency_count": 60.0,
            "latency_lost_count": 0,
            "packet_loss_pct": 0.0,
            "lag_count": 60,
        }
        measures = ResponsivenessMeasures.model_validate(data)
        assert measures.lag_avg_us == 25000
        assert measures.router_lag_avg_us is None
        assert measures.router_latency_avg_us is None
        assert measures.router_jitter_avg_us is None
        assert measures.router_latency_count is None
        assert measures.router_latency_lost_count is None
        assert measures.router_packet_loss_pct is None
        assert measures.router_lag_count is None


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


class TestScoreRecord:
    """Test ScoreRecord model."""

    def test_valid_data(self, sample_scores_data):
        """Test valid score record data."""
        record = ScoreRecord(**sample_scores_data[0])

        # Check identifiers
        assert record.orb_id == "test-orb-123"
        assert record.orb_name == "Test Orb"
        assert record.device_name == "test-device"
        assert record.timestamp == 1700000000000
        assert record.score_version == "1.0.0"
        assert record.orb_version == "2.1.0"

        # Check measures
        assert record.orb_score == 85.5
        assert record.responsiveness_score == 90.0
        assert record.reliability_score == 80.0
        assert record.speed_score == 87.5

        # Check dimensions
        assert record.network_type == 1
        assert record.country_code == "US"
        assert record.isp_name == "Test ISP"

    def test_minimal_data_identifiable_false(self):
        """Test score record with minimal fields (identifiable=false scenario)."""
        data = {
            "orb_id": "test-orb-123",
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
        }
        record = ScoreRecord.model_validate(data)
        assert record.orb_id == "test-orb-123"
        assert record.orb_name is None
        assert record.device_name is None
        assert record.city_name is None
        assert record.country_code is None
        assert record.isp_name is None
        assert record.network_state is None
        assert record.orb_score == 85.5

    def test_model_dump(self, sample_scores_data):
        """Test converting record back to dictionary."""
        record = ScoreRecord(**sample_scores_data[0])
        data = record.model_dump()

        assert isinstance(data, dict)
        assert data["orb_id"] == "test-orb-123"
        assert data["orb_score"] == 85.5

    def test_missing_required_field(self):
        """Test validation error on missing required field."""
        data = {"orb_id": "test-orb-123"}
        with pytest.raises(ValidationError):
            ScoreRecord.model_validate(data)


class TestResponsivenessRecord:
    """Test ResponsivenessRecord model."""

    def test_valid_data(self, sample_responsiveness_data):
        """Test valid responsiveness record data."""
        record = ResponsivenessRecord(**sample_responsiveness_data[0])

        # Check identifiers
        assert record.orb_id == "test-orb-123"
        assert record.orb_name == "Test Orb"
        assert record.timestamp == 1700000000000

        # Check measures
        assert record.lag_avg_us == 25000
        assert record.latency_avg_us == 30000
        assert record.packet_loss_pct == 0.0

        # Check dimensions
        assert record.network_name == "Test Network"
        assert record.network_type == 1
        assert record.pingers == "test-pinger-1,test-pinger-2"

    def test_minimal_data_identifiable_false(self):
        """Test responsiveness record with minimal fields (identifiable=false)."""
        data = {
            "orb_id": "test-orb-123",
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
        }
        record = ResponsivenessRecord.model_validate(data)
        assert record.orb_id == "test-orb-123"
        assert record.orb_name is None
        assert record.device_name is None
        assert record.network_name is None
        assert record.city_name is None
        assert record.pingers is None
        assert record.network_state is None
        assert record.lag_avg_us == 25000
        assert record.packet_loss_pct == 0.0

    def test_model_dump(self, sample_responsiveness_data):
        """Test converting record back to dictionary."""
        record = ResponsivenessRecord(**sample_responsiveness_data[0])
        data = record.model_dump()

        assert isinstance(data, dict)
        assert data["orb_id"] == "test-orb-123"
        assert data["lag_avg_us"] == 25000


class TestWebResponsivenessRecord:
    """Test WebResponsivenessRecord model."""

    def test_valid_data(self, sample_web_responsiveness_data):
        """Test valid web responsiveness record data."""
        record = WebResponsivenessRecord(**sample_web_responsiveness_data[0])

        # Check identifiers
        assert record.orb_id == "test-orb-123"
        assert record.timestamp == 1700000000000

        # Check measures
        assert record.ttfb_us == 150000
        assert record.dns_us == 50000

        # Check dimensions
        assert record.network_name == "Test Network"
        assert record.web_url == "https://example.com"

    def test_minimal_data_identifiable_false(self):
        """Test web responsiveness record with minimal fields (identifiable=false)."""
        data = {
            "orb_id": "test-orb-123",
            "timestamp": 1700000000000,
            "orb_version": "2.1.0",
            "ttfb_us": 150000,
            "dns_us": 50000,
            "network_type": 1,
        }
        record = WebResponsivenessRecord.model_validate(data)
        assert record.orb_id == "test-orb-123"
        assert record.orb_name is None
        assert record.device_name is None
        assert record.network_name is None
        assert record.city_name is None
        assert record.web_url is None
        assert record.network_state is None
        assert record.ttfb_us == 150000
        assert record.dns_us == 50000

    def test_model_dump(self, sample_web_responsiveness_data):
        """Test converting record back to dictionary."""
        record = WebResponsivenessRecord(**sample_web_responsiveness_data[0])
        data = record.model_dump()

        assert isinstance(data, dict)
        assert data["ttfb_us"] == 150000
        assert data["web_url"] == "https://example.com"


class TestSpeedRecord:
    """Test SpeedRecord model."""

    def test_valid_data(self, sample_speed_data):
        """Test valid speed record data."""
        record = SpeedRecord(**sample_speed_data[0])

        # Check identifiers
        assert record.orb_id == "test-orb-123"
        assert record.timestamp == 1700000000000

        # Check measures
        assert record.download_kbps == 50000
        assert record.upload_kbps == 10000

        # Check dimensions
        assert record.network_name == "Test Network"
        assert record.speed_test_engine == 0
        assert record.speed_test_server == "test-server-1"

    def test_minimal_data_identifiable_false(self):
        """Test speed record with minimal fields (identifiable=false scenario)."""
        data = {
            "orb_id": "test-orb-123",
            "timestamp": 1700000000000,
            "orb_version": "2.1.0",
            "download_kbps": 50000,
            "upload_kbps": 10000,
            "network_type": 1,
        }
        record = SpeedRecord.model_validate(data)
        assert record.orb_id == "test-orb-123"
        assert record.orb_name is None
        assert record.device_name is None
        assert record.network_name is None
        assert record.city_name is None
        assert record.network_state is None
        assert record.speed_test_engine is None
        assert record.speed_test_server is None
        assert record.download_kbps == 50000
        assert record.upload_kbps == 10000

    def test_model_dump(self, sample_speed_data):
        """Test converting record back to dictionary."""
        record = SpeedRecord(**sample_speed_data[0])
        data = record.model_dump()

        assert isinstance(data, dict)
        assert data["download_kbps"] == 50000
        assert data["speed_test_server"] == "test-server-1"


class TestWifiLinkMeasures:
    """Test WifiLinkMeasures model."""

    def test_valid_data(self):
        """Test valid Wi-Fi link measures data."""
        data = {
            "rssi_avg": -55.0,
            "rssi_count": 60,
            "frequency_mhz": 5180,
            "tx_rate_mbps": 300.0,
            "tx_rate_count": 60,
            "rx_rate_mbps": 270.0,
            "rx_rate_count": 60,
            "snr_avg": 40.0,
            "snr_count": 60,
            "noise_avg": -95.0,
            "noise_count": 60,
            "phy_mode": "802.11ac",
            "security": "WPA2 Personal",
            "channel_width": "80",
            "channel_number": 36,
            "channel_band": "5 GHz",
            "supported_wlan_channels": "1,6,11,36,40,44,48",
            "mcs": None,
            "nss": None,
        }
        measures = WifiLinkMeasures(**data)
        assert measures.rssi_avg == -55.0
        assert measures.rssi_count == 60
        assert measures.frequency_mhz == 5180
        assert measures.tx_rate_mbps == 300.0
        assert measures.rx_rate_mbps == 270.0
        assert measures.snr_avg == 40.0
        assert measures.noise_avg == -95.0
        assert measures.phy_mode == "802.11ac"
        assert measures.security == "WPA2 Personal"
        assert measures.channel_width == "80"
        assert measures.channel_number == 36
        assert measures.channel_band == "5 GHz"
        assert measures.mcs is None
        assert measures.nss is None

    def test_optional_platform_fields(self):
        """Test that platform-specific fields are optional."""
        data = {
            "rssi_avg": -65.0,
            "rssi_count": 15,
            "frequency_mhz": 2412,
            "tx_rate_mbps": 54.0,
            "tx_rate_count": 15,
            "rx_rate_count": 15,
            "snr_avg": 30.0,
            "snr_count": 15,
            "noise_avg": -90.0,
            "noise_count": 15,
            "phy_mode": "802.11n",
            "channel_number": 1,
            "channel_band": "2.4 GHz",
        }
        measures = WifiLinkMeasures.model_validate(data)
        assert measures.rx_rate_mbps is None
        assert measures.security is None
        assert measures.channel_width is None
        assert measures.supported_wlan_channels is None
        assert measures.mcs is None
        assert measures.nss is None

    def test_linux_only_fields(self):
        """Test mcs and nss fields (Linux only)."""
        data = {
            "rssi_avg": -50.0,
            "rssi_count": 60,
            "frequency_mhz": 5180,
            "tx_rate_mbps": 600.0,
            "tx_rate_count": 60,
            "rx_rate_count": 60,
            "snr_avg": 45.0,
            "snr_count": 60,
            "noise_avg": -95.0,
            "noise_count": 60,
            "phy_mode": "802.11ax",
            "channel_number": 36,
            "channel_band": "5 GHz",
            "mcs": 9,
            "nss": 2,
        }
        measures = WifiLinkMeasures.model_validate(data)
        assert measures.mcs == 9
        assert measures.nss == 2


class TestWifiLinkRecord:
    """Test WifiLinkRecord model."""

    def test_valid_data(self, sample_wifi_link_data):
        """Test valid Wi-Fi link record data."""
        record = WifiLinkRecord(**sample_wifi_link_data[0])

        # Check identifiers
        assert record.orb_id == "test-orb-123"
        assert record.orb_name == "Test Orb"
        assert record.timestamp == 1700000000000
        assert record.orb_version == "2.1.0"

        # Check measures
        assert record.rssi_avg == -55.0
        assert record.frequency_mhz == 5180
        assert record.tx_rate_mbps == 300.0
        assert record.snr_avg == 40.0
        assert record.phy_mode == "802.11ac"
        assert record.channel_band == "5 GHz"

        # Check dimensions
        assert record.network_type == 1
        assert record.network_name == "Test Network"
        assert record.bssid == "aa:bb:cc:dd:ee:ff"
        assert record.country_code == "US"

    def test_minimal_data_identifiable_false(self):
        """Test Wi-Fi link record with minimal fields (identifiable=false scenario)."""
        data = {
            "orb_id": "test-orb-123",
            "timestamp": 1700000000000,
            "orb_version": "2.1.0",
            "rssi_avg": -65.0,
            "rssi_count": 60,
            "frequency_mhz": 2412,
            "tx_rate_mbps": 54.0,
            "tx_rate_count": 60,
            "rx_rate_count": 60,
            "snr_avg": 30.0,
            "snr_count": 60,
            "noise_avg": -90.0,
            "noise_count": 60,
            "phy_mode": "802.11n",
            "channel_number": 1,
            "channel_band": "2.4 GHz",
            "network_type": 1,
        }
        record = WifiLinkRecord.model_validate(data)
        assert record.orb_id == "test-orb-123"
        assert record.orb_name is None
        assert record.device_name is None
        assert record.bssid is None
        assert record.mac_address is None
        assert record.network_name is None
        assert record.city_name is None
        assert record.network_state is None
        assert record.rx_rate_mbps is None
        assert record.security is None
        assert record.mcs is None
        assert record.nss is None

    def test_model_dump(self, sample_wifi_link_data):
        """Test converting record back to dictionary."""
        record = WifiLinkRecord(**sample_wifi_link_data[0])
        data = record.model_dump()

        assert isinstance(data, dict)
        assert data["orb_id"] == "test-orb-123"
        assert data["rssi_avg"] == -55.0
        assert data["channel_band"] == "5 GHz"

    def test_missing_required_field(self):
        """Test validation error on missing required field."""
        data = {"orb_id": "test-orb-123"}
        with pytest.raises(ValidationError):
            WifiLinkRecord.model_validate(data)


class TestAllDatasetsResponse:
    """Test AllDatasetsResponse model."""

    def test_valid_response(
        self,
        sample_scores_data,
        sample_responsiveness_data,
        sample_web_responsiveness_data,
        sample_speed_data,
        sample_wifi_link_data,
    ):
        """Test valid all datasets response."""
        response = AllDatasetsResponse(
            scores_1m=[ScoreRecord(**r) for r in sample_scores_data],
            responsiveness_1m=[
                ResponsivenessRecord(**r) for r in sample_responsiveness_data
            ],
            web_responsiveness=[
                WebResponsivenessRecord(**r) for r in sample_web_responsiveness_data
            ],
            speed_results=[SpeedRecord(**r) for r in sample_speed_data],
            wifi_link_1m=[WifiLinkRecord(**r) for r in sample_wifi_link_data],
        )

        assert isinstance(response.scores_1m, list)
        assert isinstance(response.responsiveness_1m, list)
        assert isinstance(response.web_responsiveness, list)
        assert isinstance(response.speed_results, list)
        assert isinstance(response.wifi_link_1m, list)

        assert len(response.scores_1m) == 2
        assert len(response.responsiveness_1m) == 1
        assert all(isinstance(r, ScoreRecord) for r in response.scores_1m)
        assert all(
            isinstance(r, ResponsivenessRecord) for r in response.responsiveness_1m
        )

    def test_response_with_error(self, sample_scores_data, sample_wifi_link_data):
        """Test all datasets response with error in one dataset."""
        from orbnet.models import ErrorPayload

        response = AllDatasetsResponse(
            scores_1m=[ScoreRecord(**r) for r in sample_scores_data],
            responsiveness_1m=ErrorPayload(error="Connection timeout"),
            web_responsiveness=[],
            speed_results=[],
            wifi_link_1m=[WifiLinkRecord(**r) for r in sample_wifi_link_data],
        )

        assert isinstance(response.scores_1m, list)
        assert isinstance(response.responsiveness_1m, ErrorPayload)
        assert response.responsiveness_1m.error == "Connection timeout"

    def test_response_with_wifi_link(
        self,
        sample_scores_data,
        sample_responsiveness_data,
        sample_web_responsiveness_data,
        sample_speed_data,
        sample_wifi_link_data,
    ):
        """Test all datasets response includes wifi_link_1m."""
        response = AllDatasetsResponse(
            scores_1m=[ScoreRecord(**r) for r in sample_scores_data],
            responsiveness_1m=[
                ResponsivenessRecord(**r) for r in sample_responsiveness_data
            ],
            web_responsiveness=[
                WebResponsivenessRecord(**r) for r in sample_web_responsiveness_data
            ],
            speed_results=[SpeedRecord(**r) for r in sample_speed_data],
            wifi_link_1m=[WifiLinkRecord(**r) for r in sample_wifi_link_data],
        )

        assert isinstance(response.wifi_link_1m, list)
        assert len(response.wifi_link_1m) == 1
        assert all(isinstance(r, WifiLinkRecord) for r in response.wifi_link_1m)

    def test_wifi_link_granular_optional(
        self,
        sample_scores_data,
        sample_responsiveness_data,
        sample_web_responsiveness_data,
        sample_speed_data,
        sample_wifi_link_data,
    ):
        """Test that wifi_link_15s and wifi_link_1s are optional."""
        response = AllDatasetsResponse(
            scores_1m=[ScoreRecord(**r) for r in sample_scores_data],
            responsiveness_1m=[
                ResponsivenessRecord(**r) for r in sample_responsiveness_data
            ],
            web_responsiveness=[
                WebResponsivenessRecord(**r) for r in sample_web_responsiveness_data
            ],
            speed_results=[SpeedRecord(**r) for r in sample_speed_data],
            wifi_link_1m=[WifiLinkRecord(**r) for r in sample_wifi_link_data],
        )

        assert response.wifi_link_15s is None
        assert response.wifi_link_1s is None

    def test_response_with_all_responsiveness(
        self,
        sample_scores_data,
        sample_responsiveness_data,
        sample_web_responsiveness_data,
        sample_speed_data,
        sample_wifi_link_data,
    ):
        """Test all datasets response with all responsiveness granularities."""
        response = AllDatasetsResponse(
            scores_1m=[ScoreRecord(**r) for r in sample_scores_data],
            responsiveness_1m=[
                ResponsivenessRecord(**r) for r in sample_responsiveness_data
            ],
            responsiveness_15s=[
                ResponsivenessRecord(**r) for r in sample_responsiveness_data
            ],
            responsiveness_1s=[
                ResponsivenessRecord(**r) for r in sample_responsiveness_data
            ],
            web_responsiveness=[
                WebResponsivenessRecord(**r) for r in sample_web_responsiveness_data
            ],
            speed_results=[SpeedRecord(**r) for r in sample_speed_data],
            wifi_link_1m=[WifiLinkRecord(**r) for r in sample_wifi_link_data],
        )

        assert response.responsiveness_1m is not None
        assert response.responsiveness_15s is not None
        assert response.responsiveness_1s is not None
        assert all(
            isinstance(r, ResponsivenessRecord) for r in response.responsiveness_1s
        )

    def test_response_with_all_wifi_link(
        self,
        sample_scores_data,
        sample_responsiveness_data,
        sample_web_responsiveness_data,
        sample_speed_data,
        sample_wifi_link_data,
    ):
        """Test all datasets response with all Wi-Fi Link granularities."""
        response = AllDatasetsResponse(
            scores_1m=[ScoreRecord(**r) for r in sample_scores_data],
            responsiveness_1m=[
                ResponsivenessRecord(**r) for r in sample_responsiveness_data
            ],
            web_responsiveness=[
                WebResponsivenessRecord(**r) for r in sample_web_responsiveness_data
            ],
            speed_results=[SpeedRecord(**r) for r in sample_speed_data],
            wifi_link_1m=[WifiLinkRecord(**r) for r in sample_wifi_link_data],
            wifi_link_15s=[WifiLinkRecord(**r) for r in sample_wifi_link_data],
            wifi_link_1s=[WifiLinkRecord(**r) for r in sample_wifi_link_data],
        )

        assert isinstance(response.wifi_link_1m, list)
        assert isinstance(response.wifi_link_15s, list)
        assert isinstance(response.wifi_link_1s, list)
        assert all(isinstance(r, WifiLinkRecord) for r in response.wifi_link_1s)


class TestErrorPayload:
    """Test ErrorPayload model and is_ok/unwrap helpers."""

    def test_error_payload_basic(self):
        from orbnet.models import ErrorPayload

        payload = ErrorPayload(error="boom")
        assert payload.error == "boom"

    def test_error_payload_serialization(self):
        from orbnet.models import ErrorPayload

        payload = ErrorPayload(error="boom")
        # exclude_none preserves the legacy bare wire format; new optional
        # fields (code, repair) default to None.
        assert payload.model_dump(exclude_none=True) == {"error": "boom"}

    def test_error_payload_validates_from_dict(self):
        from orbnet.models import ErrorPayload

        payload = ErrorPayload.model_validate({"error": "boom"})
        assert payload.error == "boom"

    def test_is_ok_with_list(self):
        from orbnet.models import is_ok

        assert is_ok([]) is True
        assert is_ok([1, 2, 3]) is True

    def test_is_ok_with_error_payload(self):
        from orbnet.models import ErrorPayload, is_ok

        assert is_ok(ErrorPayload(error="boom")) is False

    def test_unwrap_returns_list_when_ok(self):
        from orbnet.models import unwrap

        assert unwrap([1, 2, 3]) == [1, 2, 3]

    def test_unwrap_raises_on_error_payload(self):
        from orbnet.models import ErrorPayload, unwrap

        with pytest.raises(ValueError, match="Dataset failed: boom"):
            unwrap(ErrorPayload(error="boom"))

    def test_is_ok_with_none(self):
        from orbnet.models import is_ok

        assert is_ok(None) is False

    def test_unwrap_raises_on_none(self):
        from orbnet.models import unwrap

        with pytest.raises(ValueError, match="Dataset result is None"):
            unwrap(None)


@pytest.fixture
def sample_scores_data():
    """Sample scores data for testing."""
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
def sample_responsiveness_data():
    """Sample responsiveness data for testing."""
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
def sample_web_responsiveness_data():
    """Sample web responsiveness data for testing."""
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
def sample_speed_data():
    """Sample speed data for testing."""
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
            "speed_test_engine": 0,  # 0=orb, 1=iperf
            "speed_test_server": "test-server-1",
        }
    ]


@pytest.fixture
def sample_wifi_link_data():
    """Sample Wi-Fi Link dataset data for testing."""
    return [
        {
            "orb_id": "test-orb-123",
            "orb_name": "Test Orb",
            "device_name": "test-device",
            "timestamp": 1700000000000,
            "orb_version": "2.1.0",
            "rssi_avg": -55.0,
            "rssi_count": 60,
            "frequency_mhz": 5180,
            "tx_rate_mbps": 300.0,
            "tx_rate_count": 60,
            "rx_rate_mbps": 270.0,
            "rx_rate_count": 60,
            "snr_avg": 40.0,
            "snr_count": 60,
            "noise_avg": -95.0,
            "noise_count": 60,
            "phy_mode": "802.11ac",
            "security": "WPA2 Personal",
            "channel_width": "80",
            "channel_number": 36,
            "channel_band": "5 GHz",
            "supported_wlan_channels": "1,6,11,36,40,44,48",
            "mcs": None,
            "nss": None,
            "network_type": 1,
            "network_state": 1,
            "country_code": "US",
            "city_name": "San Francisco",
            "isp_name": "Test ISP",
            "public_ip": "192.168.1.100",
            "latitude": 37.7749,
            "longitude": -122.4194,
            "location_source": 1,
            "bssid": "aa:bb:cc:dd:ee:ff",
            "mac_address": "11:22:33:44:55:66",
            "network_name": "Test Network",
            "private_ip": "192.168.1.42",
            "speed_test_engine": 0,
        }
    ]


class TestAllDatasetsResponseWireFormat:
    """Verify that AllDatasetsResponse preserves the JSON wire format."""

    def test_error_field_serializes_to_error_dict(
        self, sample_scores_data, sample_wifi_link_data
    ):
        from orbnet.models import ErrorPayload

        response = AllDatasetsResponse(
            scores_1m=[ScoreRecord(**r) for r in sample_scores_data],
            responsiveness_1m=ErrorPayload(error="boom"),
            web_responsiveness=[],
            speed_results=[],
            wifi_link_1m=[WifiLinkRecord(**r) for r in sample_wifi_link_data],
        )
        # exclude_none preserves the legacy bare error wire format; the
        # extended ErrorPayload's optional code/repair default to None and
        # are omitted.
        dumped = response.model_dump(exclude_none=True)
        assert dumped["responsiveness_1m"] == {"error": "boom"}

    def test_error_field_validates_from_error_dict(
        self, sample_scores_data, sample_wifi_link_data
    ):
        from orbnet.models import ErrorPayload

        response = AllDatasetsResponse.model_validate(
            {
                "scores_1m": sample_scores_data,
                "responsiveness_1m": {"error": "boom"},
                "web_responsiveness": [],
                "speed_results": [],
                "wifi_link_1m": sample_wifi_link_data,
            }
        )
        assert isinstance(response.responsiveness_1m, ErrorPayload)
        assert response.responsiveness_1m.error == "boom"


# ---------------------------------------------------------------------------
# Error envelope: Repair + extended ErrorPayload
# ---------------------------------------------------------------------------


class TestErrorPayloadBackwardsCompat:
    """Existing wire format `{"error": "..."}` must still validate after adding
    optional `code` and `repair` fields. Pin this so future schema changes
    can't silently break consumers caching the old shape."""

    def test_legacy_payload_validates(self):
        from orbnet.models import ErrorPayload

        payload = ErrorPayload(error="connection refused")
        assert payload.error == "connection refused"
        assert payload.code is None
        assert payload.repair is None

    def test_legacy_payload_serializes_bare_when_none_excluded(self):
        from orbnet.models import ErrorPayload

        payload = ErrorPayload(error="connection refused")
        assert payload.model_dump(exclude_none=True) == {"error": "connection refused"}


class TestRepair:
    def test_minimal_construction_with_only_next_step(self):
        from orbnet.models import Repair

        r = Repair(next_step="retry with the next granularity")
        assert r.next_step == "retry with the next granularity"
        assert r.tool is None
        assert r.arguments is None
        assert r.alternative is None

    def test_full_construction(self):
        from orbnet.models import Repair

        r = Repair(
            next_step="retry with the next granularity",
            tool="orb_get_responsiveness",
            arguments={"granularity": "15s"},
        )
        assert r.tool == "orb_get_responsiveness"
        assert r.arguments == {"granularity": "15s"}

    def test_extra_fields_forbidden(self):
        from pydantic import ValidationError

        from orbnet.models import Repair

        with pytest.raises(ValidationError):
            Repair(next_step="x", bogus="y")  # type: ignore[call-arg]  # ty: ignore[unknown-argument]


class TestExtendedErrorPayload:
    def test_accepts_code_and_repair(self):
        from orbnet.models import ErrorPayload, Repair

        payload = ErrorPayload(
            error="404",
            code="granularity_unavailable",
            repair=Repair(
                next_step="retry with the next granularity",
                tool="orb_get_responsiveness",
                arguments={"granularity": "15s"},
            ),
        )
        assert payload.code == "granularity_unavailable"
        assert payload.repair is not None
        assert payload.repair.arguments == {"granularity": "15s"}

    def test_invalid_code_rejected(self):
        from pydantic import ValidationError

        from orbnet.models import ErrorPayload

        with pytest.raises(ValidationError):
            ErrorPayload(error="x", code="bogus_code")  # type: ignore[arg-type]  # ty: ignore[invalid-argument-type]
