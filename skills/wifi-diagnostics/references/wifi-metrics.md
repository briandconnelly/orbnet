# Wi-Fi Metrics Reference

## 802.11 Standard Reference

| Standard | Band | Max Theoretical | Notes |
|----------|------|-----------------|-------|
| 802.11n (Wi-Fi 4) | 2.4/5 GHz | 600 Mbps | Common on older devices |
| 802.11ac (Wi-Fi 5) | 5 GHz | 3.5 Gbps (MU-MIMO) | Most common home standard |
| 802.11ax (Wi-Fi 6) | 2.4/5 GHz | 9.6 Gbps | OFDMA, improved congestion handling |
| 802.11ax (Wi-Fi 6E) | 6 GHz | 9.6 Gbps | Less congestion, shorter range |
| 802.11be (Wi-Fi 7) | 2.4/5/6 GHz | 46 Gbps | Multi-link operation |

**Practical note:** Real-world throughput is typically 40–60% of theoretical maximum.

## Channel Plans

### 2.4 GHz Channels (US)
Channels 1–13 available; only 1, 6, and 11 are non-overlapping.

```
Ch 1:  2412 MHz  ████
Ch 2:  2417 MHz   ████   ← overlaps 1 and 3
Ch 6:  2437 MHz        ████
Ch 11: 2462 MHz              ████
```

**Problem pattern:** If `channel_number` is 2, 3, 4, 5, 7, 8, 9, or 10, the sensor is on an overlapping channel — this causes co-channel interference.

### 5 GHz Channels (US, partial)

Non-overlapping 20 MHz channels: 36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 116, 132, 136, 140, 149, 153, 157, 161, 165.

5 GHz offers ~25 non-overlapping channels — far less congestion than 2.4 GHz in dense environments.

**Channels 52–144 (DFS channels):** May require radar detection compliance, causing brief channel changes.

### 6 GHz Channels (Wi-Fi 6E/7, US)
59 non-overlapping 20 MHz channels. Least congested; not backward compatible with older devices.

## Link Rate vs. Throughput

The `tx_rate_mbps` and `rx_rate_mbps` fields show the **negotiated PHY rate**, not actual data throughput. Expect:
- Real TCP throughput ≈ 40–60% of PHY rate under ideal conditions
- TCP throughput drops significantly when RSSI < −70 dBm

### Typical PHY Rates by Standard and Signal

| Signal | 802.11n (2.4G) | 802.11ac (5G) | 802.11ax (5G) |
|--------|----------------|---------------|---------------|
| Excellent (> −50) | 300 Mbps | 866 Mbps | 1,201 Mbps |
| Good (−50 to −65) | 150 Mbps | 433 Mbps | 600 Mbps |
| Fair (−65 to −75) | 54 Mbps | 130 Mbps | 143 Mbps |
| Poor (< −75) | 6–12 Mbps | 6–54 Mbps | < 100 Mbps |

## MCS (Modulation Coding Scheme) — Linux Only

Higher MCS index = more data per transmission (requires better signal).

| MCS | Modulation | Spatial Streams | Minimum SNR |
|-----|-----------|-----------------|-------------|
| 0 | BPSK 1/2 | 1 | ~5 dB |
| 4 | 16-QAM 3/4 | 1 | ~15 dB |
| 7 | 64-QAM 5/6 | 1 | ~25 dB |
| 9 | 256-QAM (802.11ac) | 1 | ~30 dB |
| 11 | 1024-QAM (802.11ax) | 1 | ~35 dB |

Low MCS index despite good RSSI suggests high noise floor (low SNR).

## NSS (Number of Spatial Streams) — Linux Only

`nss` indicates how many MIMO spatial streams are in use:
- 1 stream: single-chain connection (lower max speed)
- 2 streams: common for mid-range devices
- 3–4 streams: high-end devices / APs

Low NSS on a device that supports multiple streams indicates poor signal or an AP that doesn't support MIMO well.

## Common RF Interference Sources

| Source | Band | Characteristics |
|--------|------|-----------------|
| Neighboring Wi-Fi | 2.4/5 GHz | Co-channel or adjacent channel interference |
| Bluetooth | 2.4 GHz | Frequency hops across 2.4 GHz band |
| Microwave ovens | 2.4 GHz | Intermittent, typically 2–3 minutes |
| Baby monitors | 2.4 GHz | Constant while operating |
| Cordless phones (DECT) | 1.9/5.8 GHz | Variable depending on protocol |
| ZigBee/Z-Wave | 2.4 GHz | Low power but can degrade SNR |

**Diagnosis:** High `noise_avg` (above −85 dBm) with low SNR indicates an RF-noisy environment, even if RSSI is adequate.

## Noise Floor Reference

`noise_avg` is the background RF noise level in dBm:

| Noise Floor | Environment |
|------------|-------------|
| < −95 dBm | Very clean RF environment |
| −95 to −85 dBm | Normal home/office |
| −85 to −75 dBm | Congested environment (dense Wi-Fi) |
| > −75 dBm | High noise; performance will suffer |

## Security Protocols

| `security` Value | Security Level | Notes |
|------------------|---------------|-------|
| WPA3 Personal | Best | SPDH, forward secrecy |
| WPA3 Enterprise | Best | 802.1X authentication |
| WPA2 Personal | Good | CCMP/AES; vulnerable to PMKID attack |
| WPA2 Enterprise | Good | 802.1X authentication |
| WPA Personal | Weak | TKIP; deprecated |
| WEP | Very weak | Broken; should not be used |
| Open | None | No encryption |

