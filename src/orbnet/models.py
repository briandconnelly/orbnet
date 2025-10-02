from typing import Callable, Literal, Optional

from pydantic import BaseModel, Field


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

    class Config:
        validate_assignment = True


class DatasetRequestParams(BaseModel):
    """Parameters for dataset requests"""

    format: Literal["json", "jsonl"] = Field(
        default="json",
        description="Response format - 'json' for array or 'jsonl' for NDJSON",
    )
    caller_id: Optional[str] = Field(
        default=None, description="Override the default caller_id for this request"
    )

    class Config:
        extra = "allow"  # Allow additional parameters


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


class PollingConfig(BaseModel):
    """Configuration for polling datasets"""

    dataset_name: str = Field(
        description="Name of the dataset to poll (e.g., 'responsiveness_1s', 'speed_results')"  # noqa: E501
    )
    interval: float = Field(
        default=60.0, gt=0, description="Seconds to wait between polls"
    )
    format: Literal["json", "jsonl"] = Field(
        default="json",
        description="Response format - 'json' for array or 'jsonl' for NDJSON",
    )
    callback: Optional[Callable] = Field(
        default=None,
        description="Optional function to call with each batch of new records",
    )
    max_iterations: Optional[int] = Field(
        default=None, ge=1, description="Maximum number of polls (None for infinite)"
    )

    class Config:
        arbitrary_types_allowed = True


class ScoreIdentifiers(BaseModel):
    """Identifiers in the Scores dataset"""

    orb_id: str = Field(description="Orb Sensor identifier")
    orb_name: str = Field(
        description="Current Orb friendly name (masked unless identifiable=true)"
    )
    device_name: str = Field(
        description="Hostname or name of the device as identified by the OS"
    )
    timestamp: int = Field(description="Interval start timestamp in epoch milliseconds")
    score_version: str = Field(description="Semantic version of scoring methodology")
    orb_version: str = Field(description="Semantic version of collecting Orb")


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
    network_state: int = Field(
        description="Speed test load state: 0=unknown, 1=idle, 2=content upload, "
        "3=peak upload, 4=content download, 5=peak download, 6=content, 7=peak"
    )
    country_code: str = Field(description="Geocoded 2-digit ISO country code")
    city_name: str = Field(description="Geocoded city name")
    isp_name: str = Field(description="ISP name from GeoIP lookup")
    public_ip: str = Field(
        description="Public IP address (masked unless identifiable=true)"
    )
    latitude: float = Field(
        description="Orb location latitude (max 2-decimals, unless identifiable=true)"
    )
    longitude: float = Field(
        description="Orb location longitude (max 2-decimals, unless identifiable=true)"
    )
    location_source: int = Field(description="Location Source: 0=unknown, 1=geoip")


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


class WebResponsivenessMeasures(BaseModel):
    """Measures in the Web Responsiveness dataset"""

    ttfb_us: int = Field(
        description="Time to First Byte loading a web page in microseconds (MAX 5000000)"  # noqa: E501
    )
    dns_us: int = Field(
        description="DNS resolver response time in microseconds (MAX 5000000)"
    )


class SpeedMeasures(BaseModel):
    """Measures in the Speed dataset"""

    download_kbps: int = Field(description="Download speed in Kbps")
    upload_kbps: int = Field(description="Upload speed in Kbps")
