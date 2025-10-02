# orbnet

A lightweight Python client for retrieving network quality data from [Orb](https://orb.net) sensors.

[![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
![PyPI - Version](https://img.shields.io/pypi/v/ami)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

`orbnet` provides a simple, async Python interface to the [Orb Local API](https://orb.net/docs/deploy-and-configure/datasets-configuration#local-api) and [Datasets](https://orb.net/docs/deploy-and-configure/datasets), allowing you to easily retrieve comprehensive network quality metrics from your Orb sensors.
You can monitor responsiveness, reliability, speed, and web performance from multiple sites with just a few lines of code.

### What is Orb?

[Orb](https://orb.net) is an intelligent network monitoring platform that continuously measures internet experience.
Unlike traditional speed tests that provide only momentary snapshots, Orb gives you real-time insights into your network's responsiveness, reliability, and speed.

## Features

- **Async/await support** - Built on `httpx` for efficient concurrent requests
- **Type safety** - Pydantic models for data validation
- **Multiple granularities** - 1-second, 15-second, and 1-minute data buckets
- **Polling support** - Automatically fetch only new records
- **Flexible formats** - JSON or JSONL output
- **Comprehensive datasets** - Scores, responsiveness, web performance, and speed tests

## Installation

```bash
pip install orbnet
```

Or using [uv](https://docs.astral.sh/uv/):

```bash
uv add orbnet
```

## Quick Start

```python
import asyncio
from orbnet import OrbAPIClient

async def main():
    # Connect to your Orb sensor
    client = OrbAPIClient(host="192.168.0.20", port=7080)
    
    # Get the latest network quality scores
    scores = await client.get_scores_1m()
    
    if scores:
        latest = scores[-1]
        print(f"Orb Score: {latest['orb_score']}")
        print(f"Responsiveness: {latest['responsiveness_score']}")
        print(f"Reliability: {latest['reliability_score']}")
        print(f"Speed: {latest['speed_score']}")

asyncio.run(main())
```

## Usage Examples

### Basic Data Retrieval

```python
from orbnet import OrbAPIClient

client = OrbAPIClient(host="192.168.0.20")

# Get 1-minute scores
scores = await client.get_scores_1m()

# Get responsiveness data (1s, 15s, or 1m granularity)
responsiveness = await client.get_responsiveness(granularity="1s")

# Get web responsiveness (TTFB and DNS)
web_data = await client.get_web_responsiveness()

# Get speed test results
speeds = await client.get_speed_results()

# Get all datasets at once
all_data = await client.get_all_datasets()
```

### Real-Time Monitoring

Monitor your network continuously with automatic polling:

```python
async def monitor_network():
    client = OrbAPIClient(host="192.168.0.20")
    
    # Poll for new data every 10 seconds
    async for records in client.poll_dataset(
        dataset_name="responsiveness_1s",
        interval=10.0
    ):
        if records:
            latest = records[-1]
            latency_ms = latest['latency_avg_us'] / 1000
            print(f"Latency: {latency_ms:.1f}ms")
```

### Alert on Network Issues

```python
def alert_callback(dataset_name, records):
    for record in records:
        # Alert on high latency
        if record['latency_avg_us'] > 50000:  # 50ms
            print(f"⚠️  High latency: {record['latency_avg_us']}μs")
        
        # Alert on packet loss
        if record['packet_loss_pct'] > 1.0:  # 1%
            print(f"⚠️  Packet loss: {record['packet_loss_pct']:.2f}%")

async def monitor_with_alerts():
    client = OrbAPIClient(host="192.168.0.20")
    
    async for _ in client.poll_dataset(
        dataset_name="responsiveness_1s",
        interval=5.0,
        callback=alert_callback
    ):
        pass  # Callback handles alerts
```

### Analyze Speed Trends

```python
async def analyze_speeds():
    client = OrbAPIClient(host="192.168.0.20")
    speeds = await client.get_speed_results()
    
    # Convert to Mbps and calculate statistics
    downloads = [s['download_kbps'] / 1000 for s in speeds]
    
    avg_speed = sum(downloads) / len(downloads)
    min_speed = min(downloads)
    max_speed = max(downloads)
    
    print(f"Download Speed Stats:")
    print(f"  Average: {avg_speed:.1f} Mbps")
    print(f"  Minimum: {min_speed:.1f} Mbps")
    print(f"  Maximum: {max_speed:.1f} Mbps")
    
    # Check SLA compliance
    required_mbps = 100
    below_sla = [s for s in downloads if s < required_mbps]
    
    if below_sla:
        pct_below = (len(below_sla) / len(downloads)) * 100
        print(f"⚠️  {pct_below:.1f}% of tests below {required_mbps} Mbps")
```

### Compare Network Performance by ISP

```python
async def compare_by_isp():
    client = OrbAPIClient(host="192.168.0.20")
    scores = await client.get_scores_1m()
    
    # Group scores by ISP
    isp_scores = {}
    for record in scores:
        isp = record['isp_name']
        if isp not in isp_scores:
            isp_scores[isp] = []
        isp_scores[isp].append(record['orb_score'])
    
    # Calculate averages
    for isp, scores_list in isp_scores.items():
        avg = sum(scores_list) / len(scores_list)
        print(f"{isp}: {avg:.1f}/100")
```

## Available Datasets

### Scores (`scores_1m`)

Overall network quality scores and component metrics (1-minute minimum granularity):

- `orb_score` - Overall quality score (0-100)
- `responsiveness_score` - Network responsiveness (0-100)
- `reliability_score` - Connection reliability (0-100)
- `speed_score` - Bandwidth score (0-100)
- Plus underlying measures: lag, download/upload speeds, etc.

### Responsiveness (`responsiveness_1s`, `responsiveness_15s`, `responsiveness_1m`)

Detailed responsiveness metrics at 1-second, 15-second, or 1-minute granularity:

- `lag_avg_us` - Average lag in microseconds
- `latency_avg_us` - Round-trip latency in microseconds
- `jitter_avg_us` - Jitter (latency variation) in microseconds
- `packet_loss_pct` - Packet loss percentage
- Router-specific metrics for local network analysis

### Web Responsiveness (`web_responsiveness_results`)

Web browsing experience metrics (once per minute):

- `ttfb_us` - Time to First Byte in microseconds
- `dns_us` - DNS resolution time in microseconds
- `web_url` - URL being tested

### Speed (`speed_results`)

Speed test results (once per hour by default):

- `download_kbps` - Download speed in Kbps
- `upload_kbps` - Upload speed in Kbps
- `speed_test_server` - Server used for testing
- `speed_test_engine` - Testing engine (Orb or iperf)

## Configuration

### Client Options

```python
client = OrbAPIClient(
    host="192.168.0.20",           # Orb sensor IP/hostname
    port=7080,                      # API port (default: 7080)
    caller_id="my-app",             # Persistent ID for polling
    client_id="MyApp/1.0.0",        # User-Agent identifier
    timeout=30.0,                   # Request timeout in seconds
)
```

### Caller ID

The `caller_id` parameter enables stateful polling - the Orb sensor tracks which records each caller has already received, returning only new data on subsequent requests. This is perfect for building real-time monitoring systems.

```python
# First request returns all available data
client = OrbAPIClient(host="192.168.0.20", caller_id="monitor-1")
data1 = await client.get_scores_1m()  # Returns: 100 records

# Second request returns only new data
data2 = await client.get_scores_1m()  # Returns: 5 new records
```

### Client ID

The `client_id` is sent as the User-Agent header and helps identify your application in Orb sensor logs:

```python
# Development
client = OrbAPIClient(
    host="192.168.0.20",
    client_id="MyApp/dev-0.1.0"
)

# Production with metadata
client = OrbAPIClient(
    host="192.168.0.20",
    client_id="MyApp/1.0.0 (production; host=server-01)"
)
```

## API Reference

### OrbAPIClient

#### Methods

- **`get_scores_1m(format="json", caller_id=None)`**  
  Retrieve 1-minute granularity Scores dataset

- **`get_responsiveness(granularity="1m", format="json", caller_id=None)`**  
  Retrieve Responsiveness dataset (1s, 15s, or 1m)

- **`get_web_responsiveness(format="json", caller_id=None)`**  
  Retrieve Web Responsiveness dataset

- **`get_speed_results(format="json", caller_id=None)`**  
  Retrieve Speed test results

- **`get_all_datasets(format="json", caller_id=None, include_all_responsiveness=False)`**  
  Retrieve all datasets concurrently

- **`poll_dataset(dataset_name, interval=60.0, format="json", callback=None, max_iterations=None)`**  
  Continuously poll a dataset at regular intervals

#### Properties

- `host` - Configured host
- `port` - Configured port
- `caller_id` - Configured caller ID
- `client_id` - Configured client ID
- `timeout` - Request timeout

## Output Formats

### JSON (default)

Returns a Python list of dictionaries:

```python
scores = await client.get_scores_1m(format="json")
# Returns: [{"orb_score": 85.5, ...}, {"orb_score": 87.2, ...}]
```

### JSONL (JSON Lines)

Returns newline-delimited JSON as a string, useful for streaming:

```python
scores = await client.get_scores_1m(format="jsonl")
# Returns: '{"orb_score": 85.5, ...}\n{"orb_score": 87.2, ...}\n'

# Parse it:
import json
for line in scores.strip().split('\n'):
    record = json.loads(line)
    print(record['orb_score'])
```

## Error Handling

```python
import httpx

try:
    client = OrbAPIClient(host="192.168.0.20", timeout=5.0)
    scores = await client.get_scores_1m()
except httpx.ConnectError:
    print("Unable to connect to Orb sensor")
except httpx.TimeoutException:
    print("Request timed out")
except httpx.HTTPStatusError as e:
    print(f"HTTP error: {e.response.status_code}")
```


## MCP Server

`orbnet` includes a [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that allows Claude and other LLM applications to access your Orb network data.


### Claude Desktop Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "orb-net": {
      "command": "uvx",
      "args": [
        "--from",
        "https://github.com/briandconnelly/orbnet.git",
        "orbnet-mcp"
      ]
      "env": {
        "ORB_HOST": "<host IP address>",
        "ORB_PORT": "7080"
      }
    }
  }
}
```


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


## Disclaimer

This is an unofficial client library and is not officially affiliated with Orb.
For official support, visit [orb.net](https://orb.net).
