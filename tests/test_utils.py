"""
Test utilities and helpers for orbnet tests.
"""

from typing import Any, Dict, List


def create_mock_orb_response(
    dataset_type: str,
    record_count: int = 2,
    timestamp_base: int = 1700000000000,
) -> List[Dict[str, Any]]:
    """
    Create mock Orb API response data for testing.

    Args:
        dataset_type: Type of dataset ('scores', 'responsiveness', 'web', 'speed',
                      'wifi')
        record_count: Number of records to generate
        timestamp_base: Base timestamp for records

    Returns:
        List of mock records
    """
    records = []

    for i in range(record_count):
        base_record = {
            "orb_id": f"test-orb-{i}",
            "orb_name": f"Test Orb {i}",
            "device_name": f"test-device-{i}",
            "timestamp": timestamp_base + (i * 60000),  # 1 minute intervals
            "orb_version": "2.1.0",
            "network_type": 1,
            "network_state": 1,
            "country_code": "US",
            "city_name": "San Francisco",
            "isp_name": f"Test ISP {i}",
            "public_ip": f"192.168.1.{100 + i}",
            "latitude": 37.7749,
            "longitude": -122.4194,
            "location_source": 1,
        }

        if dataset_type == "scores":
            record = {
                **base_record,
                "score_version": "1.0.0",
                "orb_score": 85.0 + i,
                "responsiveness_score": 90.0 + i,
                "reliability_score": 80.0 + i,
                "speed_score": 87.5 + i,
                "speed_age_ms": 0,
                "lag_avg_us": 25000.0 - (i * 1000),
                "download_avg_kbps": 50000 + (i * 1000),
                "upload_avg_kbps": 10000 + (i * 500),
                "unresponsive_ms": 0.0,
                "measured_ms": 60000.0,
                "lag_count": 60,
                "speed_count": 1,
            }
        elif dataset_type == "responsiveness":
            record = {
                **base_record,
                "network_name": f"Test Network {i}",
                "pingers": f"test-pinger-{i}",
                "lag_avg_us": 25000 - (i * 1000),
                "latency_avg_us": 30000 - (i * 1000),
                "jitter_avg_us": 2000 - (i * 100),
                "latency_count": 60.0,
                "latency_lost_count": i,
                "packet_loss_pct": (i * 0.1),
                "lag_count": 60,
                "router_lag_avg_us": 5000 - (i * 100),
                "router_latency_avg_us": 8000 - (i * 100),
                "router_jitter_avg_us": 500 - (i * 10),
                "router_latency_count": 60.0,
                "router_latency_lost_count": i,
                "router_packet_loss_pct": (i * 0.05),
                "router_lag_count": 60,
            }
        elif dataset_type == "web":
            record = {
                **base_record,
                "network_name": f"Test Network {i}",
                "web_url": f"https://example{i}.com",
                "ttfb_us": 150000 - (i * 10000),
                "dns_us": 50000 - (i * 5000),
            }
        elif dataset_type == "speed":
            record = {
                **base_record,
                "network_name": f"Test Network {i}",
                "speed_test_engine": i % 2,  # Alternate between 0 (orb) and 1 (iperf)
                "speed_test_server": f"test-server-{i}",
                "download_kbps": 50000 + (i * 1000),
                "upload_kbps": 10000 + (i * 500),
            }
        elif dataset_type == "wifi":
            record = {
                **base_record,
                "bssid": f"aa:bb:cc:dd:ee:{i:02x}",
                "mac_address": f"11:22:33:44:55:{i:02x}",
                "network_name": f"Test Network {i}",
                "private_ip": f"192.168.1.{10 + i}",
                "speed_test_engine": 0,
                "rssi_avg": -55.0 - i,
                "rssi_count": 60,
                "frequency_mhz": 5180 + (i * 20),
                "tx_rate_mbps": 300.0 - (i * 10),
                "tx_rate_count": 60,
                "rx_rate_mbps": 270.0 - (i * 10),
                "rx_rate_count": 60,
                "snr_avg": 40.0 - i,
                "snr_count": 60,
                "noise_avg": -95.0,
                "noise_count": 60,
                "phy_mode": "802.11ac",
                "security": "WPA2 Personal",
                "channel_width": "80",
                "channel_number": 36 + (i * 4),
                "channel_band": "5 GHz",
                "supported_wlan_channels": "36,40,44,48",
                "mcs": None,
                "nss": None,
            }
        else:
            raise ValueError(f"Unknown dataset type: {dataset_type}")

        records.append(record)

    return records


def assert_valid_orb_score_record(record: Dict[str, Any]) -> None:
    """
    Assert that a record has valid Orb score data structure.

    Args:
        record: Record to validate

    Raises:
        AssertionError: If record is invalid
    """
    required_fields = [
        "orb_id",
        "orb_name",
        "device_name",
        "timestamp",
        "score_version",
        "orb_version",
        "orb_score",
        "responsiveness_score",
        "reliability_score",
        "speed_score",
        "lag_avg_us",
        "download_avg_kbps",
        "upload_avg_kbps",
        "network_type",
        "country_code",
        "isp_name",
    ]

    for field in required_fields:
        assert field in record, f"Missing required field: {field}"

    # Validate score ranges
    assert 0 <= record["orb_score"] <= 100, "orb_score must be 0-100"
    assert 0 <= record["responsiveness_score"] <= 100, (
        "responsiveness_score must be 0-100"
    )  # noqa: E501
    assert 0 <= record["reliability_score"] <= 100, "reliability_score must be 0-100"
    assert 0 <= record["speed_score"] <= 100, "speed_score must be 0-100"

    # Validate numeric types
    assert isinstance(record["timestamp"], int), "timestamp must be integer"
    assert isinstance(record["orb_score"], (int, float)), "orb_score must be numeric"
    assert isinstance(record["lag_avg_us"], (int, float)), "lag_avg_us must be numeric"


def assert_valid_responsiveness_record(record: Dict[str, Any]) -> None:
    """
    Assert that a record has valid responsiveness data structure.

    Args:
        record: Record to validate

    Raises:
        AssertionError: If record is invalid
    """
    required_fields = [
        "orb_id",
        "orb_name",
        "device_name",
        "timestamp",
        "orb_version",
        "lag_avg_us",
        "latency_avg_us",
        "jitter_avg_us",
        "packet_loss_pct",
        "network_type",
    ]

    for field in required_fields:
        assert field in record, f"Missing required field: {field}"

    # Validate numeric ranges
    assert record["lag_avg_us"] >= 0, "lag_avg_us must be non-negative"
    assert record["latency_avg_us"] >= 0, "latency_avg_us must be non-negative"
    assert record["jitter_avg_us"] >= 0, "jitter_avg_us must be non-negative"
    assert 0 <= record["packet_loss_pct"] <= 100, "packet_loss_pct must be 0-100"


def assert_valid_web_responsiveness_record(record: Dict[str, Any]) -> None:
    """
    Assert that a record has valid web responsiveness data structure.

    Args:
        record: Record to validate

    Raises:
        AssertionError: If record is invalid
    """
    required_fields = [
        "orb_id",
        "orb_name",
        "device_name",
        "timestamp",
        "orb_version",
        "ttfb_us",
        "dns_us",
        "web_url",
    ]

    for field in required_fields:
        assert field in record, f"Missing required field: {field}"

    # Validate numeric ranges
    assert record["ttfb_us"] >= 0, "ttfb_us must be non-negative"
    assert record["dns_us"] >= 0, "dns_us must be non-negative"


def assert_valid_speed_record(record: Dict[str, Any]) -> None:
    """
    Assert that a record has valid speed test data structure.

    Args:
        record: Record to validate

    Raises:
        AssertionError: If record is invalid
    """
    required_fields = [
        "orb_id",
        "orb_name",
        "device_name",
        "timestamp",
        "orb_version",
        "download_kbps",
        "upload_kbps",
        "speed_test_engine",
        "speed_test_server",
    ]

    for field in required_fields:
        assert field in record, f"Missing required field: {field}"

    # Validate numeric ranges
    assert record["download_kbps"] >= 0, "download_kbps must be non-negative"
    assert record["upload_kbps"] >= 0, "upload_kbps must be non-negative"


def create_mock_error_response(error_message: str = "Test error") -> Dict[str, str]:
    """
    Create a mock error response.

    Args:
        error_message: Error message to include

    Returns:
        Error response dictionary
    """
    return {"error": error_message}


def validate_client_config(config: Dict[str, Any]) -> None:
    """
    Validate client configuration dictionary.

    Args:
        config: Configuration dictionary to validate

    Raises:
        AssertionError: If configuration is invalid
    """
    required_fields = ["host", "port", "base_url", "caller_id", "timeout"]

    for field in required_fields:
        assert field in config, f"Missing required config field: {field}"

    assert isinstance(config["host"], str), "host must be string"
    assert isinstance(config["port"], int), "port must be integer"
    assert 1 <= config["port"] <= 65535, "port must be 1-65535"
    assert isinstance(config["base_url"], str), "base_url must be string"
    assert config["base_url"].startswith("http://"), "base_url must start with http://"
    assert isinstance(config["caller_id"], str), "caller_id must be string"
    assert isinstance(config["timeout"], (int, float)), "timeout must be numeric"
    assert config["timeout"] > 0, "timeout must be positive"


def assert_valid_score_record_object(record) -> None:
    """
    Assert that a ScoreRecord Pydantic object is valid.

    Args:
        record: ScoreRecord object to validate

    Raises:
        AssertionError: If record is invalid
    """
    from orbnet.models import ScoreRecord

    assert isinstance(record, ScoreRecord), "record must be ScoreRecord instance"

    # Validate score ranges
    assert 0 <= record.orb_score <= 100, "orb_score must be 0-100"
    assert 0 <= record.responsiveness_score <= 100, "responsiveness_score must be 0-100"
    assert 0 <= record.reliability_score <= 100, "reliability_score must be 0-100"
    assert 0 <= record.speed_score <= 100, "speed_score must be 0-100"

    # Validate numeric ranges
    assert record.timestamp > 0, "timestamp must be positive"
    assert record.lag_avg_us >= 0, "lag_avg_us must be non-negative"


def assert_valid_responsiveness_record_object(record) -> None:
    """
    Assert that a ResponsivenessRecord Pydantic object is valid.

    Args:
        record: ResponsivenessRecord object to validate

    Raises:
        AssertionError: If record is invalid
    """
    from orbnet.models import ResponsivenessRecord

    assert isinstance(record, ResponsivenessRecord), (
        "record must be ResponsivenessRecord instance"
    )

    # Validate numeric ranges
    assert record.lag_avg_us >= 0, "lag_avg_us must be non-negative"
    assert record.latency_avg_us >= 0, "latency_avg_us must be non-negative"
    assert record.jitter_avg_us >= 0, "jitter_avg_us must be non-negative"
    assert 0 <= record.packet_loss_pct <= 100, "packet_loss_pct must be 0-100"


def assert_valid_web_responsiveness_record_object(record) -> None:
    """
    Assert that a WebResponsivenessRecord Pydantic object is valid.

    Args:
        record: WebResponsivenessRecord object to validate

    Raises:
        AssertionError: If record is invalid
    """
    from orbnet.models import WebResponsivenessRecord

    assert isinstance(record, WebResponsivenessRecord), (
        "record must be WebResponsivenessRecord instance"
    )

    # Validate numeric ranges
    assert record.ttfb_us >= 0, "ttfb_us must be non-negative"
    assert record.dns_us >= 0, "dns_us must be non-negative"
    assert record.web_url.startswith(("http://", "https://")), (
        "web_url must be valid URL"
    )


def assert_valid_speed_record_object(record) -> None:
    """
    Assert that a SpeedRecord Pydantic object is valid.

    Args:
        record: SpeedRecord object to validate

    Raises:
        AssertionError: If record is invalid
    """
    from orbnet.models import SpeedRecord

    assert isinstance(record, SpeedRecord), "record must be SpeedRecord instance"

    # Validate numeric ranges
    assert record.download_kbps >= 0, "download_kbps must be non-negative"
    assert record.upload_kbps >= 0, "upload_kbps must be non-negative"
    assert record.speed_test_engine in [0, 1], (
        "speed_test_engine must be 0 (orb) or 1 (iperf)"
    )


def assert_valid_wifi_link_record(record: Dict[str, Any]) -> None:
    """
    Assert that a record has valid Wi-Fi Link data structure.

    Args:
        record: Record dict to validate

    Raises:
        AssertionError: If record is invalid
    """
    required_fields = [
        "orb_id",
        "timestamp",
        "orb_version",
        "rssi_avg",
        "rssi_count",
        "tx_rate_mbps",
        "tx_rate_count",
        "rx_rate_count",
        "snr_avg",
        "snr_count",
        "noise_avg",
        "noise_count",
        "phy_mode",
        "channel_number",
        "channel_band",
        "network_type",
    ]

    for field in required_fields:
        assert field in record, f"Missing required field: {field}"

    # Validate numeric ranges (RSSI and noise are negative dBm values)
    assert record["rssi_avg"] <= 0, "rssi_avg must be non-positive (dBm)"
    assert record["snr_avg"] >= 0, "snr_avg must be non-negative (dB)"
    assert record["noise_avg"] <= 0, "noise_avg must be non-positive (dBm)"
    assert record["rssi_count"] >= 0, "rssi_count must be non-negative"
    assert record["tx_rate_mbps"] >= 0, "tx_rate_mbps must be non-negative"
    assert isinstance(record["timestamp"], int), "timestamp must be integer"


def assert_valid_wifi_link_record_object(record) -> None:
    """
    Assert that a WifiLinkRecord Pydantic object is valid.

    Args:
        record: WifiLinkRecord object to validate

    Raises:
        AssertionError: If record is invalid
    """
    from orbnet.models import WifiLinkRecord

    assert isinstance(record, WifiLinkRecord), "record must be WifiLinkRecord instance"

    # Validate numeric ranges
    assert record.rssi_avg <= 0, "rssi_avg must be non-positive (dBm)"
    assert record.snr_avg >= 0, "snr_avg must be non-negative (dB)"
    assert record.noise_avg <= 0, "noise_avg must be non-positive (dBm)"
    assert record.tx_rate_mbps >= 0, "tx_rate_mbps must be non-negative"
    assert record.timestamp > 0, "timestamp must be positive"
    if record.rx_rate_mbps is not None:
        assert record.rx_rate_mbps >= 0, "rx_rate_mbps must be non-negative"
    if record.mcs is not None:
        assert record.mcs >= 0, "mcs must be non-negative"
    if record.nss is not None:
        assert record.nss >= 0, "nss must be non-negative"
