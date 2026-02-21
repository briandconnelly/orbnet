---
name: Orb Wi-Fi Diagnostics
description: This skill should be used when the user asks about Wi-Fi signal strength, "is my Wi-Fi good", "why is my Wi-Fi weak or slow", "what Wi-Fi channel am I on", "is there Wi-Fi interference", "my Wi-Fi is fast but internet is slow", "is the problem my Wi-Fi or my ISP", "why does my Wi-Fi drop", "Wi-Fi vs ethernet", or when the get_wifi_link MCP tool is being called or its results are being analyzed. Provides interpretation of Wi-Fi signal metrics (RSSI, SNR, link rates), channel and band analysis, interference diagnosis, and correlation with overall network performance.
---

# Orb Wi-Fi Diagnostics

## Overview

Wi-Fi Link data measures the wireless connection between the Orb sensor and its access point. Use `get_wifi_link` to analyze signal quality, channel conditions, and link layer performance, then correlate with overall network metrics to distinguish Wi-Fi problems from WAN/ISP issues.

**Availability note:** Wi-Fi Link data is not available when the Orb sensor is connected via ethernet or running on iOS. Some fields are platform-specific — see Platform Caveats below.

## Reading Orb Configuration

Check `orbs.json` in the project root for configured Orbs (see the network-quality skill for format). For Wi-Fi diagnostics, a specific Orb is usually implied by the user's question; ask if ambiguous.

## Fetching Wi-Fi Data

```
get_wifi_link(granularity="1m")     # trends and analysis
get_wifi_link(granularity="1s")     # real-time signal fluctuations
get_wifi_link(granularity="15s")    # balance between resolution and noise
```

An empty list means the sensor is on ethernet or iOS. Inform the user: this confirms the Orb is not on Wi-Fi, which rules out wireless signal issues as the cause of any reported problems.

## Signal Strength (RSSI)

`rssi_avg` is reported in dBm (decibel-milliwatts). Higher (less negative) is better.

| RSSI (dBm) | Rating | Meaning |
|------------|--------|---------|
| > −50 | Excellent | Very strong; full throughput |
| −50 to −65 | Good | Reliable; typical for most use cases |
| −65 to −75 | Fair | Usable but degraded throughput likely |
| −75 to −85 | Poor | Frequent dropouts; unreliable for streaming |
| < −85 | Very poor | Barely connected; significant packet loss expected |

## Signal-to-Noise Ratio (SNR)

`snr_avg` measures the ratio of signal to background RF noise in dB. Higher is better.

| SNR (dB) | Rating |
|----------|--------|
| > 40 | Excellent |
| 25–40 | Good |
| 15–25 | Fair — interference likely |
| < 15 | Poor — performance severely impacted |

Low SNR with acceptable RSSI suggests high background RF noise (interference), not weak signal.

## Link Rates

`tx_rate_mbps` (transmit) and `rx_rate_mbps` (receive) indicate the negotiated wireless link speed.

- Link rate is the **maximum possible** throughput — actual data throughput will be lower
- Low link rates relative to the Wi-Fi standard indicate poor signal quality
- 802.11ac (Wi-Fi 5): up to 866 Mbps single-stream, ~1,300 Mbps for 3-stream on 5 GHz (theoretical)
- 802.11ax (Wi-Fi 6/6E): max ~9,600 Mbps theoretical

If link rates are significantly below the standard's maximum, signal quality is limiting bandwidth.

## Channel and Band Analysis

| Field | Meaning |
|-------|---------|
| `channel_band` | 2.4 GHz or 5 GHz (or 6 GHz for Wi-Fi 6E) |
| `channel_number` | Specific channel in use |
| `frequency_mhz` | Channel center frequency |
| `phy_mode` | Wi-Fi standard (802.11n, 802.11ac, 802.11ax, etc.) |
| `channel_width` | Channel width in MHz (not available on Android) |

**2.4 GHz vs 5 GHz:**
- 2.4 GHz: longer range, more congestion/interference, max 3 non-overlapping channels
- 5 GHz: shorter range, less interference, ~25 non-overlapping channels (region-dependent)
- 6 GHz (Wi-Fi 6E): least congestion, shortest range

**Channel overlap (2.4 GHz):** Channels 1, 6, and 11 are the only non-overlapping ones. If the sensor is on 2.4 GHz channel 3 or 9, it's overlapping with neighboring networks.

## Correlation Patterns

Use these patterns to identify root causes:

| Pattern | Likely Cause | Recommendation |
|---------|-------------|----------------|
| Low RSSI + high latency | Device too far from AP | Move sensor or AP closer |
| Low SNR + packet loss | RF interference | Change channel, use 5 GHz |
| Low link rate + slow speed | Signal quality bottlenecking | Improve signal (position, obstacles) |
| Good RSSI/SNR but slow speed | WAN/ISP issue | Check `get_speed_results` vs plan |
| Intermittent drops | Channel congestion or interference | Scan for neighboring networks |

## Cross-Metric Correlation

Always combine Wi-Fi data with network-level data for conclusive diagnosis:

1. Call `get_wifi_link(granularity="1m")` for signal history
2. Call `get_responsiveness(granularity="1m")` and look for correlation between low RSSI/SNR periods and high latency or packet loss
3. Call `get_speed_results` — if speed is low only when RSSI is poor, Wi-Fi is the bottleneck; if speed is consistently low regardless of RSSI, the issue is upstream
4. Timestamps are in epoch milliseconds — align data from different tools by timestamp to find correlations

**Wi-Fi vs WAN diagnosis:**
- Low RSSI/SNR *and* poor responsiveness → Wi-Fi is the problem
- Good RSSI/SNR *but* poor responsiveness → WAN or ISP is the problem
- Intermittent drops in RSSI *correlating* with latency spikes → wireless instability

## Platform Caveats

| Field | Availability |
|-------|-------------|
| `rx_rate_mbps` | Not available on macOS |
| `security` | Not available on Android |
| `channel_width` | Not available on Android |
| `mcs` (modulation coding scheme) | Linux only |
| `nss` (spatial streams) | Linux only |

Omit unavailable fields gracefully — don't report them as zero or unknown; simply don't include them in the analysis.

## Presenting Wi-Fi Findings

- Report RSSI as "−65 dBm (Good)" with both the value and rating
- Report SNR as "32 dB (Good)"
- Always state the band (2.4/5 GHz) and channel — this is immediately actionable
- If using 2.4 GHz, check if a 5 GHz network is available — recommend switching if signal quality permits
- End with ranked recommendations: Wi-Fi-layer fixes first, then network-level suggestions

## Additional Resources

For detailed 802.11 standard rates, channel plans, and interference sources:
- **`references/wifi-metrics.md`** — 802.11 standard reference, channel plans, noise sources
