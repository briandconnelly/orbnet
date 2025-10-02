# Orb Network MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that provides Claude and other LLM applications with access to real-time network quality data from [Orb](https://orb.net) sensors.

## Installation

Install the package with MCP support:

```bash
# Using uv (recommended)
cd /Users/bdc/projects/orbnet
uv pip install -e ".[mcp]"

# Or using pip
pip install -e ".[mcp]"
```

## Running the Server

There are multiple ways to run the MCP server:

### 1. Using the installed command (recommended)

After installation with the `mcp` extra:

```bash
export ORB_HOST="192.168.0.20"
export ORB_PORT="7080"
orbnet-mcp
```

### 2. As a Python module

```bash
export ORB_HOST="192.168.0.20"
export ORB_PORT="7080"
python -m orbnet.mcp_server
```

### 3. Using the convenience wrapper

```bash
export ORB_HOST="192.168.0.20"
export ORB_PORT="7080"
python server.py
```

## Configuration

### Environment Variables

- `ORB_HOST` - Orb sensor hostname or IP address (default: `localhost`)
- `ORB_PORT` - Orb API port number (default: `7080`)

### Claude Desktop Configuration

Add this to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "orb-net": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/bdc/projects/orbnet",
        "run",
        "orbnet-mcp"
      ],
      "env": {
        "ORB_HOST": "192.168.0.20",
        "ORB_PORT": "7080"
      }
    }
  }
}
```

Alternatively, if installed globally:

```json
{
  "mcpServers": {
    "orb-net": {
      "command": "orbnet-mcp",
      "env": {
        "ORB_HOST": "192.168.0.20",
        "ORB_PORT": "7080"
      }
    }
  }
}
```

## Available Tools

The MCP server exposes 6 tools for retrieving Orb network quality data:

### `get_scores_1m`

Retrieve 1-minute granularity overall network quality scores including Orb Score and its component scores (Responsiveness, Reliability, Speed).

**Example queries:**
- "What's my current network quality score?"
- "Show me the network scores from the last hour"

### `get_responsiveness`

Retrieve detailed network responsiveness metrics including lag, latency, jitter, and packet loss. Available in 1-second, 15-second, or 1-minute granularity.

**Parameters:**
- `granularity` - Time bucket size: "1s", "15s", or "1m" (default: "1m")

**Example queries:**
- "Show me responsiveness data with 1-second granularity"
- "What's the current latency and packet loss?"
- "Are there any jitter issues?"

### `get_web_responsiveness`

Retrieve web browsing performance metrics including Time to First Byte (TTFB) and DNS resolution times.

**Example queries:**
- "How fast is my DNS resolver responding?"
- "What's the time to first byte for web pages?"

### `get_speed_results`

Retrieve speed test results including download and upload bandwidth measurements.

**Example queries:**
- "What were my recent download and upload speeds?"
- "Show me the last speed test results"

### `get_all_datasets`

Retrieve all datasets concurrently for comprehensive network analysis.

**Parameters:**
- `include_all_responsiveness` - If True, includes 1s, 15s, and 1m responsiveness data (default: False)

**Example queries:**
- "Give me a complete overview of my network performance"
- "Show me all network metrics"

### `get_client_info`

Get information about the current Orb API client configuration.

**Example queries:**
- "What Orb sensor am I connected to?"
- "Show me the current MCP server configuration"

## Stateful Polling

The MCP server uses **stateful polling** with a session-specific `caller_id`:

- **First query**: Returns all available historical data
- **Subsequent queries**: Returns only new data collected since the last query
- **After restart**: New session ID, starts fresh with all data

This makes follow-up queries efficient - no duplicate data when asking "tell me more" or checking for updates.

### Example Workflow

```
You: "What's my current network quality?"
Claude: [Fetches all historical scores, shows recent data]

You: "Show me any new scores"
Claude: [Fetches only new scores since last query - efficient!]

[Restart MCP server]

You: "What's my current network quality?"
Claude: [New session, fetches all historical scores again]
```

## Common Parameters

All data retrieval tools support these optional parameters:

- `host` - Override the Orb sensor hostname/IP
- `port` - Override the API port
- `caller_id` - Custom ID for polling state (advanced use)
- `timeout` - Request timeout in seconds (default: 30.0)

## Understanding the Data

### Network Quality Scores (0-100)

- **90-100**: Excellent - Network performing optimally
- **70-89**: Good - Minor issues, generally good experience
- **50-69**: Fair - Noticeable issues affecting user experience
- **Below 50**: Poor - Significant problems requiring attention

### Latency Guidelines

- **< 20ms**: Excellent for real-time applications
- **20-50ms**: Good for most applications
- **50-100ms**: Acceptable for general browsing
- **> 100ms**: Noticeable delays

### Packet Loss

- **0%**: Ideal
- **< 1%**: Generally acceptable
- **1-2.5%**: Noticeable in real-time apps
- **> 2.5%**: Significant quality degradation

### Network Types

- `0`: Unknown
- `1`: WiFi
- `2`: Ethernet
- `3`: Other

## Example Queries

Once configured in Claude, you can ask:

- "What's my current network quality?"
- "Show me the latency measurements from the past hour"
- "Are there any packet loss issues?"
- "Compare my download speeds over time"
- "What's the jitter on my connection?"
- "How long does DNS resolution take?"
- "Give me a comprehensive network health report"
- "Compare router latency vs internet latency"

## Troubleshooting

### Can't connect to Orb sensor

- Verify `ORB_HOST` is correct
- Ensure the Orb sensor is powered on and connected
- Test connectivity: `ping 192.168.0.20`
- Check firewall rules

### No data returned

- Orb sensor may need time to collect data after starting
- Some datasets run less frequently (speed tests are hourly by default)
- Check if the Orb sensor is actively monitoring

### Permission or port issues

- Ensure the Orb Local API is enabled on your sensor
- Verify the port number (default: 7080)
- Check firewall rules if using a custom port

### Import errors

Make sure you installed the MCP extras:
```bash
uv pip install -e ".[mcp]"
```

## Development

The MCP server is located at `src/orbnet/mcp_server.py` and is part of the orbnet package.

To make changes:

1. Edit `src/orbnet/mcp_server.py`
2. The changes take effect immediately (no reinstall needed with `-e` install)
3. Restart Claude Desktop to reload the MCP server

## License

MIT License - see [LICENSE](LICENSE) for details.

## Disclaimer

This is an unofficial MCP server and is not officially affiliated with Orb or Anthropic.

- Orb: [orb.net](https://orb.net)
- MCP: [modelcontextprotocol.io](https://modelcontextprotocol.io)
