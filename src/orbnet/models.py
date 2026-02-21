from typing import Callable, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

NETWORK_STATE_DESC = (
    "Speed test load state: 0=unknown, 1=idle, 2=content upload, "
    "3=peak upload, 4=content download, 5=peak download, 6=content, 7=peak (may not be included)"  # noqa: E501
)

LOCATION_SOURCE_DESC = "Location Source: 0=unknown, 1=geoip (may not be included)"


class OrbClientConfig(BaseModel):
    """Configuration for the Orb API Client"""

    host: str = Field(
        description="Hostname or IP address of the Orb sensor",
    )
    port: int = Field(
        default=7080, ge=1, le=65535, description="Port number for the Orb API"
    )
    caller_id: Optional[str] = Field(
        default=None,
        description="Unique ID for this caller to track polling state. If None, generates a random UUID.",  # noqa: E501
    )
    client_id: Optional[str] = Field(
        default=None,
        description="Optional identifier for the HTTP client itself (sent as User-Agent header). If None, uses a default.",  # noqa: E501
    )
    timeout: float = Field(default=30.0, gt=0, description="Request timeout in seconds")

    model_config = ConfigDict(validate_assignment=True)


class DatasetRequestParams(BaseModel):
    """Parameters for dataset requests"""

    caller_id: Optional[str] = Field(
        default=None, description="Override the default caller_id for this request"
    )

    model_config = ConfigDict(extra="allow")


class ResponsivenessRequestParams(DatasetRequestParams):
    """Parameters for responsiveness dataset requests"""

    granularity: Literal["1s", "15s", "1m"] = Field(
        default="1m", description="Time bucket size - '1s', '15s', or '1m'"
    )


class AllDatasetsRequestParams(DatasetRequestParams):
    """Parameters for fetching all datasets"""

    include_all_responsiveness: bool = Field(
        default=False,
        description="If True, fetches all responsiveness granularities (1s, 15s, 1m). If False, only fetches 1m.",  # noqa: E501
    )
    include_all_wifi_link: bool = Field(
        default=False,
        description="If True, fetches all Wi-Fi Link granularities (1s, 15s, 1m). If False, only fetches 1m.",  # noqa: E501
    )


class PollingConfig(BaseModel):
    """Configuration for polling datasets"""

    dataset_name: str = Field(
        description="Name of the dataset to poll (e.g., 'responsiveness_1s', 'speed_results')"  # noqa: E501
    )
    interval: float = Field(
        default=60.0, gt=0, description="Seconds to wait between polls"
    )
    callback: Optional[Callable] = Field(
        default=None,
        description="Optional function to call with each batch of new records",
    )
    max_iterations: Optional[int] = Field(
        default=None, ge=1, description="Maximum number of polls (None for infinite)"
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)


# ============================================================================
# Base Classes
# ============================================================================


class BaseIdentifiers(BaseModel):
    """Base identifiers common across most datasets"""

    orb_id: str = Field(description="Orb Sensor identifier")
    orb_name: Optional[str] = Field(
        default=None, description="Current Orb friendly name (may not be included)"
    )
    device_name: Optional[str] = Field(
        default=None,
        description="Hostname or name of the device as identified by the OS (may not be included)",  # noqa: E501
    )
    orb_version: str = Field(description="Semantic version of collecting Orb")
    timestamp: int = Field(description="Timestamp in epoch milliseconds")


# ============================================================================
# Dataset Models - Identifiers, Measures, and Dimensions
# ============================================================================


class ScoreIdentifiers(BaseIdentifiers):
    """Identifiers in the Scores dataset"""

    timestamp: int = Field(
        description="Interval start timestamp in epoch milliseconds"
    )  # Override for different description
    score_version: str = Field(description="Semantic version of scoring methodology")


class ScoreMeasures(BaseModel):
    """Measures in the Scores dataset"""

    orb_score: float = Field(description="Orb Score over interval (0-100)")
    responsiveness_score: float = Field(
        description="Responsiveness Score over interval (0-100)"
    )
    reliability_score: float = Field(
        description="Reliability Score over interval (0-100)"
    )
    speed_score: float = Field(
        description="Speed (Bandwidth) Score over interval (0-100)"
    )
    speed_age_ms: int = Field(
        description="Age of speed used in milliseconds, if not in timeframe. If in timeframe, 0."  # noqa: E501
    )
    lag_avg_us: float = Field(
        description="Lag in microseconds (MAX 5000000 at which point the lag considered 'unresponsive')"  # noqa: E501
    )
    download_avg_kbps: int = Field(description="Content download speed in Kbps")
    upload_avg_kbps: int = Field(description="Content upload speed in Kbps")
    unresponsive_ms: float = Field(
        description="Time spent in unresponsive state in Milliseconds"
    )
    measured_ms: float = Field(
        description="Time spent actively measuring in Milliseconds"
    )
    lag_count: int = Field(description="Count of Lag samples included")
    speed_count: int = Field(description="Count of speed samples included")


class NetworkDimensions(BaseModel):
    """Network dimensions common across datasets"""

    network_type: int = Field(
        description="Network interface type: 0=unknown, 1=wifi, 2=ethernet, 3=other"
    )
    country_code: Optional[str] = Field(
        default=None,
        description="Geocoded 2-digit ISO country code (may not be included)",
    )
    city_name: Optional[str] = Field(
        default=None, description="Geocoded city name (may not be included)"
    )
    isp_name: Optional[str] = Field(
        default=None, description="ISP name from GeoIP lookup (may not be included)"
    )
    public_ip: Optional[str] = Field(
        default=None, description="Public IP address (may not be included)"
    )
    latitude: Optional[float] = Field(
        default=None,
        description="Orb location latitude",
    )
    longitude: Optional[float] = Field(
        default=None,
        description="Orb location longitude",
    )
    location_source: Optional[int] = Field(
        default=None,
        description=LOCATION_SOURCE_DESC,
    )


class ScoreDimensions(NetworkDimensions):
    """Dimensions specific to the Scores dataset"""

    network_state: Optional[int] = Field(default=None, description=NETWORK_STATE_DESC)


class ResponsivenessMeasures(BaseModel):
    """Measures in the Responsiveness dataset"""

    lag_avg_us: int = Field(description="Avg Lag in microseconds (MAX 5000000)")
    latency_avg_us: int = Field(
        description="Avg round trip latency in microseconds for successful round trip"
    )
    jitter_avg_us: int = Field(
        description="Avg Interpacket interarrival difference (jitter) in microseconds"
    )
    latency_count: float = Field(
        description="Count of round trip latency measurements that succeeded"
    )
    latency_lost_count: int = Field(
        description="Count of round trip latency measurements that were lost"
    )
    packet_loss_pct: float = Field(
        description="latency_lost_count / (latency_count+latency_loss_count)"
    )
    lag_count: int = Field(description="Lag sample count")
    router_lag_avg_us: int = Field(description="Avg router lag in microseconds")
    router_latency_avg_us: int = Field(
        description="Avg router round trip latency in microseconds"
    )
    router_jitter_avg_us: int = Field(description="Avg router jitter in microseconds")
    router_latency_count: float = Field(
        description="Count of router latency measurements that succeeded"
    )
    router_latency_lost_count: int = Field(
        description="Count of router latency measurements that were lost"
    )
    router_packet_loss_pct: float = Field(description="Router packet loss percentage")
    router_lag_count: int = Field(description="Router lag sample count")


class ResponsivenessDimensions(NetworkDimensions):
    """Dimensions specific to the Responsiveness dataset"""

    network_name: Optional[str] = Field(
        default=None, description="Network name (SSID, if available)"
    )
    network_state: Optional[int] = Field(default=None, description=NETWORK_STATE_DESC)
    pingers: Optional[str] = Field(
        default=None,
        description="List (CSV) of {protocol}|{endpoint} (may not be included)",
    )


class WebResponsivenessMeasures(BaseModel):
    """Measures in the Web Responsiveness dataset"""

    ttfb_us: int = Field(
        description="Time to First Byte loading a web page in microseconds (MAX 5000000)"  # noqa: E501
    )
    dns_us: int = Field(
        description="DNS resolver response time in microseconds (MAX 5000000)"
    )


class WebResponsivenessDimensions(NetworkDimensions):
    """Dimensions specific to the Web Responsiveness dataset"""

    network_name: Optional[str] = Field(
        default=None, description="Network name (SSID, if available)"
    )
    network_state: Optional[int] = Field(default=None, description=NETWORK_STATE_DESC)
    web_url: Optional[str] = Field(
        default=None, description="URL endpoint for web test (may not be included)"
    )


class SpeedMeasures(BaseModel):
    """Measures in the Speed dataset"""

    download_kbps: int = Field(description="Download speed in Kbps")
    upload_kbps: int = Field(description="Upload speed in Kbps")


class SpeedDimensions(NetworkDimensions):
    """Dimensions specific to the Speed dataset"""

    network_name: Optional[str] = Field(
        default=None, description="Network name (SSID, if available)"
    )
    network_state: Optional[int] = Field(default=None, description=NETWORK_STATE_DESC)
    speed_test_engine: Optional[int] = Field(
        default=None, description="Testing engine: 0=orb, 1=iperf (may not be included)"
    )
    speed_test_server: Optional[str] = Field(
        default=None, description="Server URL or identifier (may not be included)"
    )


class WifiLinkMeasures(BaseModel):
    """Measures in the Wi-Fi Link dataset"""

    rssi_avg: float = Field(description="Average received signal strength in dBm")
    rssi_count: int = Field(description="Count of successful RSSI measurements")
    frequency_mhz: Optional[int] = Field(
        default=None, description="Connected channel frequency in MHz (may not be included)"
    )
    tx_rate_mbps: Optional[float] = Field(
        default=None, description="Average transmit link rate in Mbps"
    )
    tx_rate_count: Optional[int] = Field(
        default=None, description="Count of transmit rate measurements"
    )
    rx_rate_mbps: Optional[float] = Field(
        default=None,
        description="Average receive link rate in Mbps (unavailable on macOS)",
    )
    rx_rate_count: Optional[int] = Field(
        default=None, description="Count of receive rate measurements"
    )
    snr_avg: float = Field(description="Average signal-to-noise ratio in dB")
    snr_count: int = Field(description="Count of SNR measurements")
    noise_avg: float = Field(description="Average background RF noise level in dBm")
    noise_count: int = Field(description="Count of noise measurements")
    phy_mode: str = Field(
        description="Wi-Fi standard designation (e.g., 802.11n, 802.11ac, 802.11ax)"
    )
    security: Optional[str] = Field(
        default=None,
        description="Wi-Fi security protocol (unavailable on Android)",
    )
    channel_width: Optional[str] = Field(
        default=None,
        description="Channel width in MHz (unavailable on Android)",
    )
    channel_number: int = Field(description="Wi-Fi channel number")
    channel_band: str = Field(description="Wi-Fi band designation")
    supported_wlan_channels: Optional[str] = Field(
        default=None,
        description="Comma-separated list of supported WLAN channels (unavailable on Windows)",  # noqa: E501
    )
    mcs: Optional[int] = Field(
        default=None,
        description="Modulation and coding scheme index (Linux only)",
    )
    nss: Optional[int] = Field(
        default=None,
        description="Number of spatial streams (Linux only)",
    )


class WifiLinkDimensions(NetworkDimensions):
    """Dimensions specific to the Wi-Fi Link dataset"""

    bssid: Optional[str] = Field(
        default=None, description="Access point MAC address (may not be included)"
    )
    mac_address: Optional[str] = Field(
        default=None, description="Client MAC address (may not be included)"
    )
    network_name: Optional[str] = Field(
        default=None, description="Network name / SSID (may not be included)"
    )
    network_state: Optional[int] = Field(default=None, description=NETWORK_STATE_DESC)
    private_ip: Optional[str] = Field(
        default=None, description="Local IP address (may not be included)"
    )
    speed_test_engine: Optional[int] = Field(
        default=None, description="Testing engine: 0=orb, 1=iperf (may not be included)"
    )


# ============================================================================
# Complete Dataset Records
# ============================================================================


class BaseRecord(BaseModel):
    """Base record with common configuration"""

    model_config = ConfigDict(extra="allow")


class ScoreRecord(BaseRecord, ScoreIdentifiers, ScoreMeasures, ScoreDimensions):
    """
    Complete record from the Scores dataset (scores_1m).

    Combines identifiers, measures, and dimensions into a single flat structure
    matching the API response format.
    """

    timestamp: int = Field(description="Interval start timestamp in epoch milliseconds")


class ResponsivenessRecord(
    BaseRecord,
    BaseIdentifiers,
    ResponsivenessMeasures,
    ResponsivenessDimensions,
):
    """
    Complete record from the Responsiveness dataset (responsiveness_1s/15s/1m).

    Combines identifiers, measures, and dimensions into a single flat structure
    matching the API response format.
    """

    pass


class WebResponsivenessRecord(
    BaseRecord,
    BaseIdentifiers,
    WebResponsivenessMeasures,
    WebResponsivenessDimensions,
):
    """
    Complete record from the Web Responsiveness dataset (web_responsiveness_results).

    Combines identifiers, measures, and dimensions into a single flat structure
    matching the API response format.
    """

    pass


class SpeedRecord(BaseRecord, BaseIdentifiers, SpeedMeasures, SpeedDimensions):
    """
    Complete record from the Speed dataset (speed_results).

    Combines identifiers, measures, and dimensions into a single flat structure
    matching the API response format.
    """

    pass


class WifiLinkRecord(BaseRecord, BaseIdentifiers, WifiLinkMeasures, WifiLinkDimensions):
    """
    Complete record from the Wi-Fi Link dataset (wifi_link_1s/15s/1m).

    Combines identifiers, measures, and dimensions into a single flat structure
    matching the API response format.

    Note: Wi-Fi Link dataset fields are not available on iOS. Field availability
    varies by platform: macOS does not include rx_rate_mbps; Android does not
    include security or channel_width; Windows does not include
    supported_wlan_channels; mcs and nss are Linux only.
    """

    pass


# ============================================================================
# All Datasets Response
# ============================================================================


class AllDatasetsResponse(BaseModel):
    """
    Response containing all datasets.

    Each dataset field contains either a list of records or an error dict
    if that dataset failed to fetch.
    """

    scores_1m: List[ScoreRecord] | dict
    responsiveness_1m: List[ResponsivenessRecord] | dict
    responsiveness_15s: Optional[List[ResponsivenessRecord] | dict] = None
    responsiveness_1s: Optional[List[ResponsivenessRecord] | dict] = None
    web_responsiveness: List[WebResponsivenessRecord] | dict
    speed_results: List[SpeedRecord] | dict
    wifi_link_1m: List[WifiLinkRecord] | dict
    wifi_link_15s: Optional[List[WifiLinkRecord] | dict] = None
    wifi_link_1s: Optional[List[WifiLinkRecord] | dict] = None

    model_config = ConfigDict(extra="allow")
