---
name: Orb Network Quality Analysis
description: This skill should be used when the user asks about network quality, internet performance, Orb scores, connection health, latency, jitter, packet loss, speed test results, web performance, Wi-Fi signal strength, or wireless link quality, or when the user says "analyze my network", "check my internet", "why is my internet slow", "is my connection good for video calls", "show me my network history", "what's my Orb score", "troubleshoot my internet", "what's my Wi-Fi signal strength", "check my RSSI", or "analyze my Wi-Fi channel", or when analyzing data from the orbnet MCP tools (get_scores_1m, get_responsiveness, get_speed_results, get_web_responsiveness, get_wifi_link, get_all_datasets, get_client_info).
---

# Orb Network Quality Analysis

## Overview

The orbnet MCP server exposes tools for fetching real-time and historical network quality data from Orb sensors. Always attribute results to the specific Orb sensor, not the user's own device — an Orb may be monitoring a different network segment.

## Reading Orb Configuration

Before making tool calls, check whether `orbs.json` exists in the project root. If present, read it to discover available Orbs:

```json
{
  "default": "living-room",
  "orbs": {
    "living-room": { "host": "192.168.1.100", "port": 7080 },
    "office":       { "host": "192.168.1.101", "port": 7080 }
  }
}
```

When multiple Orbs are configured:
- Use the `default` field to select the Orb when the user doesn't specify one
- Ask the user which Orb to query if context is ambiguous
- Pass `host` and `port` explicitly in each tool call

If no settings file exists, use MCP server defaults (localhost, port 7080), or ask the user for the sensor's address.

## Tool Selection Guide

| Goal | Best Tool | Notes |
|------|-----------|-------|
| Quick health check | `get_scores_1m` | Fastest; overall picture |
| Video/VoIP issues | `get_responsiveness` | Lag, jitter, packet loss |
| Slow downloads/uploads | `get_speed_results` | Bandwidth focus |
| Slow web browsing | `get_web_responsiveness` | TTFB and DNS performance |
| Full diagnosis | `get_all_datasets` | Fetches all datasets in parallel |
| Wi-Fi signal / channel quality | `get_wifi_link` | RSSI, SNR, phy_mode, channel |
| Verify sensor connection | `get_client_info` | Check host, port, caller_id |

## Interpreting Orb Scores

The Orb Score (0–100) represents overall network health:

| Score | Rating | Meaning |
|-------|--------|---------|
| 90–100 | Excellent | Outstanding performance |
| 80–89 | Good | Minor room for improvement |
| 70–79 | OK | Noticeable room for improvement |
| 50–69 | Fair | Noticeable issues |
| 0–49 | Poor | Needs attention |

Component scores (responsiveness_score, reliability_score, speed_score) follow the same scale. A low component score identifies exactly where to dig deeper.

## Stateful Polling

The MCP server uses a session-fixed `caller_id` for stateful polling:
- First call returns all available historical data
- Subsequent calls in the same session return only new records

To reset polling and retrieve all data again, pass a new UUID as `caller_id`. This is useful when switching Orbs or starting a fresh analysis.

## Responsiveness Thresholds

| Metric | Unit | Good | Fair | Poor |
|--------|------|------|------|------|
| `lag_avg_us` | µs | < 20,000 | 20,000–50,000 | > 50,000 |
| `latency_avg_us` | µs | < 50,000 | 50,000–100,000 | > 100,000 |
| `jitter_avg_us` | µs | < 10,000 | 10,000–30,000 | > 30,000 |
| `packet_loss_pct` | % | < 1 | 1–5 | > 5 |

Use `granularity="1s"` for real-time troubleshooting; `"1m"` for trend analysis.

## Speed Test Notes

Speed tests run approximately once per hour. Convert `download_kbps` and `upload_kbps` to Mbps by dividing by 1,000. Compare against the user's subscribed plan when available — if the user hasn't mentioned their plan speed, ask before drawing conclusions about whether results are acceptable.

## Web Responsiveness Thresholds

| Metric | Unit | Good | Poor |
|--------|------|------|------|
| `ttfb_us` | µs | < 500,000 (500 ms) | > 1,000,000 (1 s) |
| `dns_us` | µs | < 50,000 (50 ms) | > 200,000 (200 ms) |

High TTFB suggests server-side or WAN latency; high DNS time suggests a DNS resolver problem.

## Analysis Workflow

For a complete diagnosis:

1. Call `get_scores_1m` to get an overall picture
2. Check which component scores are low and drill into that dataset
3. Look for patterns over time — degradation during peak hours suggests congestion
4. Correlate metrics:
   - High latency + packet loss → congestion or ISP issue
   - High jitter → instability, likely affects VoIP and video
   - Low speed but good responsiveness → bandwidth bottleneck, not latency
   - Slow DNS but fast TTFB → DNS resolver problem
   - All scores low → likely upstream WAN or ISP issue
   - Low speed or high latency + poor RSSI or low `tx_rate_mbps` → wireless layer bottleneck, not WAN
5. Summarize findings with specific metric values and actionable recommendations
6. Attribute all findings to the Orb sensor, not the user's device

## Presenting Results

When reporting to the user:
- Convert microseconds to milliseconds (divide by 1,000) for readability
- Convert kbps to Mbps (divide by 1,000) for speed values
- Include timestamps to anchor results in time
- Lead with the Orb Score and its trend, then drill into specifics
- End with concrete next steps (e.g., "Check ISP status", "Move device closer to router")

## Additional Resources

For complete field definitions and all available metrics across each dataset, see:
- **`references/metrics.md`** — Detailed field reference for all datasets
