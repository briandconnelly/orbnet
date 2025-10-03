#!/usr/bin/env python3
"""
Orb Network MCP Server

A Model Context Protocol server that provides access to Orb network quality datasets.
Uses the orbnet package to retrieve data from Orb sensors.

Stateful Polling:
    This server uses a fixed caller_id for the lifetime of the server process.
    This means:
    - First query returns all available historical data
    - Subsequent queries in the same session return only new data
    - Server restart generates a new caller_id and starts fresh

    You can override the default caller_id in any tool call if you need different
    polling behavior.
"""

import os
import uuid
from typing import Any, Dict, List, Literal, Optional

from fastmcp import FastMCP

from .client import OrbAPIClient

# Initialize FastMCP server
mcp = FastMCP(
    "Orb Network Quality Data",
    instructions="""
    This server provides real-time network quality data from Orb sensors.
    
    **When to use this server:**
    - Monitor network performance metrics (latency, jitter, packet loss)
    - Track internet speed test results over time
    - Analyze web responsiveness (TTFB, DNS times)
    - Get comprehensive network quality scores
    
    **Key Features:**
    - Stateful polling: First call returns historical data, subsequent calls
                        return only new data
    - Multiple time granularities (1s, 15s, 1m) for different analysis needs
    - Concurrent data fetching for efficiency
    
    **Common use cases:**
    - "Show me my current network quality"
    - "Has my internet been stable today?"
    - "What was my average latency over the past hour?"
    - "Compare speed test results from this morning vs now"
    """,
)

# Configuration from environment variables
ORB_HOST = os.getenv("ORB_HOST", "localhost")
ORB_PORT = int(os.getenv("ORB_PORT", "7080"))

# Generate a fixed caller_id for this MCP server instance
# This enables stateful polling within a session while starting fresh on restart
DEFAULT_CALLER_ID = str(uuid.uuid4())


def get_client(
    host: str = ORB_HOST,
    port: Optional[int] = None,
    caller_id: Optional[str] = None,
    timeout: Optional[float] = None,
) -> OrbAPIClient:
    """Create an OrbAPIClient with required host and optional overrides."""
    return OrbAPIClient(
        host=host,
        port=port or ORB_PORT,
        caller_id=caller_id or DEFAULT_CALLER_ID,
        timeout=timeout or 30.0,
    )


@mcp.tool()
async def get_scores_1m(
    host: str = ORB_HOST,
    port: Optional[int] = None,
    caller_id: Optional[str] = None,
    timeout: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve 1-minute granularity Scores dataset from an Orb sensor.

    The Scores Dataset includes Orb Score and its component scores (Responsiveness,
    Reliability, and Speed), along with underlying network quality measures.

    The Orb score represents the overall health of your network using
    measurements of responsiveness, reliability, and speed.

        - Responsiveness: How quickly and consistently a network responds
                          to requests
        - Reliability: How consistent and dependable the network is
        - Speed: How fast a network can transfer data to and from
                 a device

    A higher Orb Score indicates better overall performance.
    Scores can be interpreted as follows:

        - 90-100: Excellent performance and quality
        - 80-89: Good performance with room for improvement
        - 70-79: Ok performance with room for improvement
        - 50-59: Fair performance with noticeable issues
        - 0-49: Poor performance that needs attention


    Note on Stateful Polling:
        By default, this tool uses a session-specific caller_id. This means your
        first call returns all available data, and subsequent calls return only
        new data collected since the last call. This makes it efficient to check
        for updates without receiving duplicate records.

    Args:
        host: Orb sensor hostname or IP (default: from ORB_HOST env var or 'localhost')
        port: API port number (default: from ORB_PORT env var or 7080)
        caller_id: Unique ID to track polling state. Leave as None to use the default
                   session-specific ID, or provide your own for custom polling behavior.
        timeout: Request timeout in seconds (default: 30.0)

    Returns:
        List of score records, each containing:
        - orb_score: Overall network quality score (0-100)
        - responsiveness_score: Network responsiveness score (0-100)
        - reliability_score: Network reliability score (0-100)
        - speed_score: Network speed score (0-100)
        - lag_avg_us: Average lag in microseconds
        - download_avg_kbps: Average download speed in kbps
        - upload_avg_kbps: Average upload speed in kbps
        - network_type: Network interface type (0=Unknown, 1=Wi-Fi, 2=Ethernet)
        - isp_name: Internet service provider name
        - country_code: Two-letter country code
        - timestamp: Measurement timestamp in epoch milliseconds
        - And more...
    """
    client = get_client(host, port, caller_id, timeout)
    return await client.get_scores_1m(format="json")


@mcp.tool()
async def get_responsiveness(
    host: str = ORB_HOST,
    granularity: Literal["1s", "15s", "1m"] = "1m",
    port: Optional[int] = None,
    caller_id: Optional[str] = None,
    timeout: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve Responsiveness dataset from an Orb sensor.

    Includes detailed network responsiveness measures including lag, latency,
    jitter, and packet loss. Available in 1-second, 15-second, and 1-minute buckets.

    Note on Stateful Polling:
        By default, this tool uses a session-specific caller_id. This means your
        first call returns all available data, and subsequent calls return only
        new data collected since the last call. This makes it efficient to check
        for updates without receiving duplicate records.

    Args:
        granularity: Time bucket size - '1s', '15s', or '1m' (default: '1m')
        host: Orb sensor hostname or IP (default: from ORB_HOST env var or 'localhost')
        port: API port number (default: from ORB_PORT env var or 7080)
        caller_id: Unique ID to track polling state. Leave as None to use the default
                   session-specific ID, or provide your own for custom polling behavior.
        timeout: Request timeout in seconds (default: 30.0)

    Returns:
        List of responsiveness records, each containing:
        - lag_avg_us: Average lag in microseconds
        - latency_avg_us: Average round-trip latency in microseconds
        - jitter_avg_us: Average jitter in microseconds
        - packet_loss_pct: Packet loss percentage
        - latency_count: Number of successful latency measurements
        - latency_lost_count: Number of lost packets
        - router_lag_avg_us: Average lag to router in microseconds
        - router_latency_avg_us: Average router round-trip latency in microseconds
        - router_packet_loss_pct: Router packet loss percentage
        - timestamp: Measurement timestamp in epoch milliseconds
        - And more...
    """
    client = get_client(host, port, caller_id, timeout)
    return await client.get_responsiveness(granularity=granularity, format="json")


@mcp.tool()
async def get_web_responsiveness(
    host: str = ORB_HOST,
    port: Optional[int] = None,
    caller_id: Optional[str] = None,
    timeout: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve Web Responsiveness dataset from an Orb sensor.

    Includes Time to First Byte (TTFB) for web page loads and DNS resolver
    response time. Measurements are conducted once per minute by default.

    Note on Stateful Polling:
        By default, this tool uses a session-specific caller_id. This means your
        first call returns all available data, and subsequent calls return only
        new data collected since the last call. This makes it efficient to check
        for updates without receiving duplicate records.

    Args:
        host: Orb sensor hostname or IP (default: from ORB_HOST env var or 'localhost')
        port: API port number (default: from ORB_PORT env var or 7080)
        caller_id: Unique ID to track polling state. Leave as None to use the default
                   session-specific ID, or provide your own for custom polling behavior.
        timeout: Request timeout in seconds (default: 30.0)

    Returns:
        List of web responsiveness records, each containing:
        - ttfb_us: Time to First Byte in microseconds (max 5,000,000)
        - dns_us: DNS resolver response time in microseconds (max 5,000,000)
        - web_url: URL that was tested
        - timestamp: Measurement timestamp in epoch milliseconds
        - network_type: Network interface type
        - And more...
    """
    client = get_client(host, port, caller_id, timeout)
    return await client.get_web_responsiveness(format="json")


@mcp.tool()
async def get_speed_results(
    host: str = ORB_HOST,
    port: Optional[int] = None,
    caller_id: Optional[str] = None,
    timeout: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve Speed test results dataset from an Orb sensor.

    Includes download and upload speed test results. Content speed measurements
    are conducted once per hour by default.

    Note on Stateful Polling:
        By default, this tool uses a session-specific caller_id. This means your
        first call returns all available data, and subsequent calls return only
        new data collected since the last call. This makes it efficient to check
        for updates without receiving duplicate records.

    Args:
        host: Orb sensor hostname or IP (default: from ORB_HOST env var or 'localhost')
        port: API port number (default: from ORB_PORT env var or 7080)
        caller_id: Unique ID to track polling state. Leave as None to use the default
                   session-specific ID, or provide your own for custom polling behavior.
        timeout: Request timeout in seconds (default: 30.0)

    Returns:
        List of speed test records, each containing:
        - download_kbps: Download speed in kbps
        - upload_kbps: Upload speed in kbps
        - speed_test_engine: Name of the speed test engine used
        - speed_test_server: Server used for the speed test
        - timestamp: Test timestamp in epoch milliseconds
        - network_type: Network interface type
        - And more...
    """
    client = get_client(host, port, caller_id, timeout)
    return await client.get_speed_results(format="json")


@mcp.tool()
async def get_all_datasets(
    host: str = ORB_HOST,
    include_all_responsiveness: bool = False,
    port: Optional[int] = None,
    caller_id: Optional[str] = None,
    timeout: Optional[float] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Retrieve all available datasets from an Orb sensor concurrently.

    Fetches scores, responsiveness, web responsiveness, and speed test datasets
    in parallel for efficiency.

    Note on Stateful Polling:
        By default, this tool uses a session-specific caller_id. This means your
        first call returns all available data, and subsequent calls return only
        new data collected since the last call. This makes it efficient to check
        for updates without receiving duplicate records.

    Args:
        include_all_responsiveness: If True, fetches all responsiveness granularities
                                   (1s, 15s, 1m). If False, only fetches 1m. (default:
                                   False)
        host: Orb sensor hostname or IP (default: from ORB_HOST env var or 'localhost')
        port: API port number (default: from ORB_PORT env var or 7080)
        caller_id: Unique ID to track polling state. Leave as None to use the default
                   session-specific ID, or provide your own for custom polling behavior.
        timeout: Request timeout in seconds (default: 30.0)

    Returns:
        Dictionary with keys for each dataset type:
        - scores_1m: 1-minute scores dataset
        - responsiveness_1m: 1-minute responsiveness dataset
        - responsiveness_15s: 15-second responsiveness if
            (include_all_responsiveness=True)
        - responsiveness_1s: 1-second responsiveness
            (if include_all_responsiveness=True)
        - web_responsiveness: Web responsiveness results
        - speed_results: Speed test results

        Each value is either a list of records or an error dict if that dataset failed.
    """
    client = get_client(host, port, caller_id, timeout)
    return await client.get_all_datasets(
        format="json", include_all_responsiveness=include_all_responsiveness
    )


def _get_client_info_impl(
    host: str = ORB_HOST,
    port: Optional[int] = None,
    caller_id: Optional[str] = None,
    timeout: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Get information about the Orb API client configuration.

    Returns details about the current client settings including host, port,
    caller_id, and other configuration parameters. Useful for debugging or
    verifying which Orb sensor you're connected to.

    Args:
        host: Orb sensor hostname or IP
        port: API port number (default: from ORB_PORT env var or 7080)
        caller_id: Unique ID to track polling state. Leave as None to see the default
                   session-specific ID that's being used.
        timeout: Request timeout in seconds (default: 30.0)

    Returns:
        Dictionary containing:
        - host: Configured Orb sensor hostname/IP
        - port: Configured API port
        - base_url: Full base URL for API requests
        - caller_id: Caller ID being used for polling state tracking
        - timeout: Request timeout in seconds
    """
    client = get_client(host, port, caller_id, timeout)
    return {
        "host": client.host,
        "port": client.port,
        "base_url": client.base_url,
        "caller_id": client.caller_id,
        "timeout": client.timeout,
    }


@mcp.tool()
def get_client_info(
    host: str = ORB_HOST,
    port: Optional[int] = None,
    caller_id: Optional[str] = None,
    timeout: Optional[float] = None,
) -> Dict[str, Any]:
    """Get information about the Orb API client configuration."""
    return _get_client_info_impl(host, port, caller_id, timeout)


@mcp.prompt()
def analyze_network_quality() -> str:
    """Analyze current network quality for the configured Orb and provide insights"""
    return """
    Analyze the network quality using these steps:
    1. Call get_scores_1m() to get the latest Orb scores
    2. Examine orb_score (0-100, higher is better)
    3. Check component scores: responsiveness_score, reliability_score, speed_score
    4. If scores are low, call get_responsiveness() for detailed metrics
    5. Provide actionable insights about network performance
    """


@mcp.prompt()
def troubleshoot_slow_internet() -> str:
    """Diagnose slow internet connection issues"""
    return """
    To troubleshoot slow internet:
    1. Call get_speed_results() to check recent speed tests
    2. Call get_responsiveness(granularity="1m") for latency/jitter data
    3. Call get_web_responsiveness() to check TTFB and DNS performance
    4. Compare metrics against typical values:
       - Good latency: < 50ms
       - Good jitter: < 10ms
       - Acceptable packet loss: < 1%
    5. Identify which metric is problematic and explain to the user
    """


def main():
    """Entry point for running the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
