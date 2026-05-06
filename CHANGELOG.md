# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Structured error envelope: `Repair` model, `OrbErrorCode` literal,
  `translate_exception` dispatch, granularity-fallback repair hints, and
  MCP tool return-type widening to `list[X] | ErrorPayload` (#27)
- Server discoverability: `Does NOT` section in instructions block,
  stateful-polling declaration, `server_fingerprint` in
  `get_client_info`, and `Prerequisites:` line on prompts (#26)
- FastMCP 3.2 support with typed `ToolAnnotations`, first-class `title=`
  and `tags=` on tools/prompts (#21)

### Changed

- Internal cleanup: tightened `DatasetSpec.granularities` typing from
  `tuple[str, ...]` to `tuple[Granularity, ...]` (and same for
  `default_granularity`), eliminating a runtime-no-op `cast` in
  `OrbAPIClient.get_all_datasets`'s partial-failure path. Also removed
  the redundant `ErrorPayload.of` classmethod — its only call site
  now invokes `translate_exception` directly. No public-API change.
- **BREAKING:** Renamed all seven MCP tools with the `orb_` service
  prefix to reduce ambiguity in multi-server contexts. `get_scores_1m`
  also drops the `_1m` suffix because the Scores dataset is
  single-granularity at the Orb API level. No deprecation aliases —
  old names are gone. Migration:
  - `get_scores_1m` → `orb_get_scores`
  - `get_responsiveness` → `orb_get_responsiveness`
  - `get_speed_results` → `orb_get_speed_results`
  - `get_web_responsiveness` → `orb_get_web_responsiveness`
  - `get_wifi_link` → `orb_get_wifi_link`
  - `get_all_datasets` → `orb_get_all_datasets`
  - `get_client_info` → `orb_get_client_info`

  Direct Python users of `OrbAPIClient` see no method-signature changes.
  Note: `ErrorPayload.repair.tool` values emitted via
  `OrbAPIClient.get_all_datasets`'s partial-failure path now reflect the
  new MCP tool names (the `tool` field is documented as the canonical
  MCP tool to retry with).
- **BREAKING:** Dropped FastMCP 2.x support; `fastmcp>=3.2.0` is now
  required (#21)
- Aligned MCP tool granularity defaults to `1m` to match the underlying
  client (the MCP layer previously defaulted to `1s` while the client
  defaulted to `1m`, producing different behavior depending on entry
  point) (#25)
- Tightened FastMCP `instructions` to carry only client-actionable
  information; dropped Transport, Auth, Server-fingerprint, and
  env-var Ambient-state lines added in #26. The fingerprint remains
  surfaced via `get_client_info` (#28)
- Modernized typing to Python 3.13 conventions (#24)
- Lazy config loading; tightened `PollingCallback` typing (#23)

### Fixed

- Correctness bugs in client and MCP server: granularity validation
  and host validation at the boundary (#22)

## [0.2.0] - 2026-02-21

### Added

- Wi-Fi Link dataset support (#4)
- Coverage reporting via new `check_coverage` CI workflow (#3)

## [0.1.3] - 2025-10-05

### Changed

- Return Pydantic objects from client methods (#2)

## [0.1.2] - 2025-10-03

### Changed

- MCP server discoverability: server instructions, tool annotations, MCP resources, and config validation (#1)

## [0.1.0] - 2025-10-02

### Added

- Initial release.
