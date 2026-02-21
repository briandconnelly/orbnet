# Orb Network Metrics Reference

## Scores Dataset (`get_scores_1m`)

1-minute granularity only. Each record represents a 1-minute aggregate.

| Field | Type | Unit | Description |
|-------|------|------|-------------|
| `orb_score` | float | 0–100 | Overall network quality score |
| `responsiveness_score` | float | 0–100 | Responsiveness component score |
| `reliability_score` | float | 0–100 | Reliability component score |
| `speed_score` | float | 0–100 | Speed component score |
| `lag_avg_us` | float | µs | Average lag in microseconds |
| `download_avg_kbps` | int | kbps | Average download throughput |
| `upload_avg_kbps` | int | kbps | Average upload throughput |
| `network_type` | int | enum | 0=Unknown, 1=Wi-Fi, 2=Ethernet, 3=Other |
| `isp_name` | str | — | Internet service provider name |
| `country_code` | str | — | Two-letter ISO country code |
| `timestamp` | int | epoch ms | Measurement timestamp |

## Responsiveness Dataset (`get_responsiveness`)

Available granularities: `1s`, `15s`, `1m`.

| Field | Type | Unit | Description |
|-------|------|------|-------------|
| `lag_avg_us` | int | µs | Average lag (round-trip from device to internet) |
| `latency_avg_us` | int | µs | Average round-trip latency |
| `jitter_avg_us` | int | µs | Average jitter (variation in latency) |
| `packet_loss_pct` | float | % | Percentage of lost packets |
| `latency_count` | int | — | Number of successful latency measurements |
| `latency_lost_count` | int | — | Number of lost packets |
| `router_lag_avg_us` | int | µs | Average lag to local router |
| `router_latency_avg_us` | int | µs | Average round-trip latency to router |
| `router_packet_loss_pct` | float | % | Packet loss to router |
| `network_type` | int | enum | 0=Unknown, 1=Wi-Fi, 2=Ethernet, 3=Other |
| `timestamp` | int | epoch ms | Measurement timestamp |

**Lag vs. Latency:** Lag measures time until the first byte response; latency is the full round-trip time. Lag is typically lower than latency.

**Router metrics:** Compares against the local router, not the internet. High router lag can indicate a congested home network; high internet lag with normal router lag points to ISP issues.

## Speed Dataset (`get_speed_results`)

Runs approximately once per hour.

| Field | Type | Unit | Description |
|-------|------|------|-------------|
| `download_kbps` | int | kbps | Download speed from speed test |
| `upload_kbps` | int | kbps | Upload speed from speed test |
| `speed_test_engine` | int | enum | Engine used: 0=orb, 1=iperf |
| `speed_test_server` | str | — | Server endpoint used |
| `network_type` | int | enum | 0=Unknown, 1=Wi-Fi, 2=Ethernet, 3=Other |
| `timestamp` | int | epoch ms | Test timestamp |

**Unit conversion:** Divide kbps by 1,000 for Mbps.

## Web Responsiveness Dataset (`get_web_responsiveness`)

Runs approximately once per minute.

| Field | Type | Unit | Description |
|-------|------|------|-------------|
| `ttfb_us` | int | µs | Time to First Byte for web page load (max 5,000,000) |
| `dns_us` | int | µs | DNS resolver response time (max 5,000,000) |
| `web_url` | str | — | URL tested |
| `network_type` | int | enum | 0=Unknown, 1=Wi-Fi, 2=Ethernet, 3=Other |
| `timestamp` | int | epoch ms | Measurement timestamp |

**Max values:** Both `ttfb_us` and `dns_us` cap at 5,000,000 µs (5 seconds), indicating a timeout.

## Wi-Fi Link Dataset (`get_wifi_link`)

Available granularities: `1s`, `15s`, `1m`.

| Field | Type | Unit | Description | Platform |
|-------|------|------|-------------|----------|
| `rssi_avg` | float | dBm | Average signal strength | All |
| `snr_avg` | float | dB | Average signal-to-noise ratio | All |
| `noise_avg` | float | dBm | Average background RF noise | All |
| `tx_rate_mbps` | float | Mbps | Transmit link rate | All |
| `rx_rate_mbps` | float | Mbps | Receive link rate | Not macOS |
| `phy_mode` | str | — | Wi-Fi standard (802.11n/ac/ax) | All |
| `channel_band` | str | — | Band (2.4 GHz, 5 GHz, 6 GHz) | All |
| `channel_number` | int | — | Wi-Fi channel number | All |
| `frequency_mhz` | int | MHz | Channel center frequency | All |
| `channel_width` | str | MHz | Channel width | Not Android |
| `security` | str | — | Security protocol (WPA2, WPA3, etc.) | Not Android |
| `network_name` | str | — | SSID of connected network | All |
| `bssid` | str | — | Access point MAC address | All |
| `mcs` | int | — | Modulation coding scheme index | Linux only |
| `nss` | int | — | Number of spatial streams | Linux only |
| `network_type` | int | enum | 0=Unknown, 1=Wi-Fi, 2=Ethernet, 3=Other | All |
| `timestamp` | int | epoch ms | Measurement timestamp | All |

## `get_all_datasets` Response Structure

Returns an `AllDatasetsResponse` with these keys:

| Key | Content | Notes |
|-----|---------|-------|
| `scores_1m` | List of ScoreRecord | Always fetched |
| `responsiveness_1m` | List of ResponsivenessRecord | Always fetched |
| `responsiveness_15s` | List of ResponsivenessRecord | Only if `include_all_responsiveness=True` |
| `responsiveness_1s` | List of ResponsivenessRecord | Only if `include_all_responsiveness=True` |
| `web_responsiveness` | List of WebResponsivenessRecord | Always fetched |
| `speed_results` | List of SpeedRecord | Always fetched |
| `wifi_link_1m` | List of WifiLinkRecord | Always fetched (empty if on ethernet/iOS) |
| `wifi_link_15s` | List of WifiLinkRecord | Only if `include_all_wifi_link=True` |
| `wifi_link_1s` | List of WifiLinkRecord | Only if `include_all_wifi_link=True` |

Each value may be a list of records or an error dict `{"error": "..."}` if that dataset failed.

## `network_type` Enum Values

| Value | Meaning |
|-------|---------|
| 0 | Unknown |
| 1 | Wi-Fi |
| 2 | Ethernet |
| 3 | Other |

## Unit Conversions Quick Reference

| From | To | Operation |
|------|----|-----------|
| kbps | Mbps | ÷ 1,000 |
| µs | ms | ÷ 1,000 |
| µs | s | ÷ 1,000,000 |
| epoch ms | human time | Convert using datetime |
