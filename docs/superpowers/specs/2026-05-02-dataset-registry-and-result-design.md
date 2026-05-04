# Dataset Registry and Result Type — Design Spec

**Date:** 2026-05-02
**Status:** Draft, pending user review
**Scope:** `src/orbnet/client.py`, `src/orbnet/models.py`, `src/orbnet/mcp_server.py`, plus a new `src/orbnet/datasets.py` module.

## Problem

Two related architectural frictions in `orbnet`:

**Dataset metadata is duplicated three ways.** Each dataset's name, granularity options, record class, and request-param shape is rewritten across:

1. Six near-identical public methods on `OrbAPIClient` (each does `validate params → _get_dataset(name, params) → [RecordClass(**r) for r in raw]`).
2. A hard-coded `dataset_methods` dict inside `poll_dataset` (`client.py:704-714`) listing all 9 wire endpoints with lambdas.
3. `get_all_datasets`'s task dict (`client.py:568-587`) listing the same names a third time, with conditional granularity expansion.

Adding a dataset requires editing all three sites in lockstep.

**`AllDatasetsResponse` uses a leaky `List[X] | dict` union for partial failures.** When `get_all_datasets` catches per-dataset exceptions it stuffs `{"error": str(e)}` into the response (`client.py:591-596`). Each field is typed `List[X] | dict`. Every Python caller has to do `isinstance(field, dict) and "error" in field` to disambiguate. Tests assert on this dict shape, so renaming the key silently breaks them.

## Goals

- Single source of truth for dataset metadata.
- Adding a new dataset is one registry entry, not edits in four files.
- Replace the bare-`dict` error leak with a typed payload.
- Preserve every public API contract: client method signatures, MCP tool surface, JSON wire formats, `poll_dataset` accepted inputs, and callback contract.
- Make tests parametrize over the registry instead of repeating six near-identical setups.

## Non-goals

- No HTTP layer change. `_get_dataset`, headers, timeouts, retries are untouched.
- No breaking change to client method names or signatures.
- No breaking change to JSON wire format of `AllDatasetsResponse`.
- No breaking change to MCP tool surface.
- No full Ousterhout-style encapsulation of the success/error union behind a wrapping container. Callers still pattern-match `isinstance(field, list)` vs `isinstance(field, ErrorPayload)` — see Section 8 rationale.
- No fold-in of the `tests/test_models.py` ↔ `tests/conftest.py` fixture duplication. Out of scope.

## Design

### 1. New `src/orbnet/datasets.py`

Single home for dataset metadata. Exports `DatasetSpec`, `DATASETS`, `POLL_ALIASES`, and `parse_poll_alias`.

```python
from dataclasses import dataclass

from .models import (
    BaseRecord, ScoreRecord, ResponsivenessRecord,
    WebResponsivenessRecord, SpeedRecord, WifiLinkRecord,
)


@dataclass(frozen=True)
class DatasetSpec:
    family: str                                # registry key
    record_class: type[BaseRecord]
    granularities: tuple[str, ...] = ()        # () means non-granular
    default_granularity: str | None = None     # set iff granularities is non-empty
    wire_name_override: str | None = None      # set iff wire name diverges from family

    def wire_name(self, granularity: str | None = None) -> str:
        if self.wire_name_override is not None:
            return self.wire_name_override
        if self.granularities:
            return f"{self.family}_{granularity or self.default_granularity}"
        return self.family

    def response_field(self, granularity: str | None = None) -> str:
        if self.granularities:
            return f"{self.family}_{granularity or self.default_granularity}"
        return self.family
```

`response_field()` is the single source for which `AllDatasetsResponse` slot to populate. It diverges from `wire_name()` only for `web_responsiveness` (wire `web_responsiveness_results`, field `web_responsiveness`).

### 2. Registry contents

```python
DATASETS: dict[str, DatasetSpec] = {
    "scores":             DatasetSpec("scores",             ScoreRecord,             granularities=("1m",),           default_granularity="1m"),
    "responsiveness":     DatasetSpec("responsiveness",     ResponsivenessRecord,    granularities=("1s","15s","1m"), default_granularity="1m"),
    "web_responsiveness": DatasetSpec("web_responsiveness", WebResponsivenessRecord, wire_name_override="web_responsiveness_results"),
    "speed_results":      DatasetSpec("speed_results",      SpeedRecord),
    "wifi_link":          DatasetSpec("wifi_link",          WifiLinkRecord,          granularities=("1s","15s","1m"), default_granularity="1m"),
}
```

`scores` is declared as a granular family with one granularity; the public shim `get_scores_1m()` simply doesn't accept a granularity argument from callers, so the public API is unchanged. The internal registry stays uniform.

### 3. `POLL_ALIASES` and `parse_poll_alias`

`poll_dataset` accepts wire-name strings today, including `web_responsiveness_results`. The accepted input space must be preserved exactly. An explicit alias table is built once at module load:

```python
POLL_ALIASES: dict[str, tuple[DatasetSpec, str | None]] = _build_poll_aliases(DATASETS)

def parse_poll_alias(name: str) -> tuple[DatasetSpec, str | None]:
    if name not in POLL_ALIASES:
        raise ValueError(
            f"Unknown dataset: {name}. Valid options: {', '.join(sorted(POLL_ALIASES))}"
        )
    return POLL_ALIASES[name]
```

`_build_poll_aliases` enumerates each spec: for granular families, one entry per `(spec, granularity)` keyed by `spec.wire_name(granularity)`; for non-granular families, one entry keyed by `spec.wire_name()` (which honors `wire_name_override`). The resulting set of accepted aliases is identical to the current `dataset_methods` keys at `client.py:704-714`.

### 4. `_fetch` helper on `OrbAPIClient`

The one place where `[spec.record_class(**r) for r in raw]` lives.

```python
async def _fetch(
    self,
    spec: DatasetSpec,
    granularity: str | None = None,
    caller_id: str | None = None,
) -> list[BaseRecord]:
    raw = await self._get_dataset(
        spec.wire_name(granularity),
        caller_id=caller_id or self.caller_id,
    )
    return [spec.record_class(**record) for record in raw]
```

`_fetch` does no input validation. Callers (the shims and `get_all_datasets`) are responsible for ensuring `granularity` is valid for the spec; the validation source of truth stays with the existing `<X>RequestParams` Pydantic models invoked in the shims (Section 5).

### 5. Public method shims

Each of the six public methods stays as today externally. Internally each becomes a thin shim over `_fetch`. Per-method validation via `<X>RequestParams` Pydantic models is preserved — direct callers of `get_responsiveness("foo")` still get a `ValidationError` with the existing message, not a `ValueError` from the registry. Example:

```python
async def get_responsiveness(
    self,
    granularity: Literal["1s", "15s", "1m"] = "1m",
    caller_id: str | None = None,
) -> list[ResponsivenessRecord]:
    request = ResponsivenessRequestParams(granularity=granularity, caller_id=caller_id)
    return await self._fetch(DATASETS["responsiveness"], request.granularity, request.caller_id)
```

`get_scores_1m`, `get_web_responsiveness`, `get_speed_results`, `get_wifi_link` follow the same pattern.

### 6. `get_all_datasets` rewritten over the registry

Two-phase: build a `plan` of `(spec, granularity)` pairs from the registry × the caller's `default_granularity` × `include_all_*` flags; then `asyncio.gather` and assemble the response by `spec.response_field(granularity)`.

```python
async def get_all_datasets(
    self,
    caller_id: str | None = None,
    default_granularity: Literal["1s", "15s", "1m"] = "1m",
    include_all_responsiveness: bool = False,
    include_all_wifi_link: bool = False,
) -> AllDatasetsResponse:
    include_all_map = {
        "responsiveness": include_all_responsiveness,
        "wifi_link": include_all_wifi_link,
    }

    plan: list[tuple[DatasetSpec, str | None]] = []
    for spec in DATASETS.values():
        if not spec.granularities:
            plan.append((spec, None))
            continue
        # If the caller's default isn't supported by this family (e.g. scores
        # only offers "1m"), fall back to the spec's own default.
        chosen = (
            default_granularity
            if default_granularity in spec.granularities
            else spec.default_granularity
        )
        plan.append((spec, chosen))
        if include_all_map.get(spec.family):
            for g in spec.granularities:
                if g != chosen:
                    plan.append((spec, g))

    tasks = [self._fetch(spec, g, caller_id) for spec, g in plan]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    fields: dict[str, list[BaseRecord] | ErrorPayload] = {}
    for (spec, g), result in zip(plan, results, strict=True):
        fields[spec.response_field(g)] = (
            ErrorPayload.of(result) if isinstance(result, BaseException) else result
        )
    return AllDatasetsResponse(**fields)
```

`default_granularity` flows through as a parameter. The registry's `default_granularity` is fallback only — the MCP tool's existing `default_granularity="1s"` (`mcp_server.py:545`) continues to flow through and produces `responsiveness_1s` / `wifi_link_1s` slots in the response, exactly as today.

The `include_all_map` is the only family-name → flag mapping in the new code; it's localized to this function because the flag names (`include_all_responsiveness`, `include_all_wifi_link`) are baked into `get_all_datasets`'s public signature and can't be derived from the registry alone. If a third family ever gains an `include_all_*` flag, both the signature and this map gain a row together.

### 7. `poll_dataset` rewritten

The hard-coded `dataset_methods` dict is removed. Validation routes through `parse_poll_alias`. Crucially, the user-supplied `dataset_name` string is preserved verbatim through to user callbacks — `poll_dataset("web_responsiveness_results", callback=cb)` still calls `cb("web_responsiveness_results", records)` exactly as today.

```python
async def poll_dataset(
    self,
    dataset_name: str,
    interval: float = 60.0,
    callback: Callable | None = None,
    max_iterations: int | None = None,
):
    config = PollingConfig(
        dataset_name=dataset_name,
        interval=interval,
        callback=callback,
        max_iterations=max_iterations,
    )
    spec, granularity = parse_poll_alias(config.dataset_name)

    iteration = 0
    while config.max_iterations is None or iteration < config.max_iterations:
        try:
            records = await self._fetch(spec, granularity)
            if config.callback and records:
                if asyncio.iscoroutinefunction(config.callback):
                    await config.callback(config.dataset_name, records)
                else:
                    config.callback(config.dataset_name, records)
            yield records
            await asyncio.sleep(config.interval)
            iteration += 1
        except Exception as e:
            logger.warning("Error polling %s: %s", config.dataset_name, e)
            await asyncio.sleep(config.interval)
            iteration += 1
```

### 8. `ErrorPayload` and `DatasetResult` in `models.py`

```python
from typing import TypeAlias, TypeVar

T = TypeVar("T")


class ErrorPayload(BaseModel):
    error: str

    model_config = ConfigDict(extra="forbid")

    @classmethod
    def of(cls, exc: BaseException) -> "ErrorPayload":
        return cls(error=str(exc))


DatasetResult: TypeAlias = list[T] | ErrorPayload


def is_ok(value: list[T] | ErrorPayload) -> bool:
    return not isinstance(value, ErrorPayload)


def unwrap(value: list[T] | ErrorPayload) -> list[T]:
    if isinstance(value, ErrorPayload):
        raise ValueError(f"Dataset failed: {value.error}")
    return value
```

**Rationale for TypeAlias over wrapper container.** A wrapping `DatasetResult(BaseModel, Generic[T])` with `.records`/`.error` would break `len(field)`, iteration, and indexing on the success branch — `tests/test_models.py:835-861` and `tests/test_client.py:401-421` exercise these directly. The TypeAlias path keeps success-branch ergonomics intact and confines the breaking change to the error branch (`field["error"]` → `field.error`, `isinstance(field, dict)` → `isinstance(field, ErrorPayload)`). The full encapsulation can be revisited later as a deliberate breaking change if the union pattern becomes painful enough to warrant it.

### 9. `AllDatasetsResponse` field types

```python
class AllDatasetsResponse(BaseModel):
    scores_1m: list[ScoreRecord] | ErrorPayload
    responsiveness_1m: list[ResponsivenessRecord] | ErrorPayload | None = None
    responsiveness_15s: list[ResponsivenessRecord] | ErrorPayload | None = None
    responsiveness_1s: list[ResponsivenessRecord] | ErrorPayload | None = None
    web_responsiveness: list[WebResponsivenessRecord] | ErrorPayload
    speed_results: list[SpeedRecord] | ErrorPayload
    wifi_link_1m: list[WifiLinkRecord] | ErrorPayload | None = None
    wifi_link_15s: list[WifiLinkRecord] | ErrorPayload | None = None
    wifi_link_1s: list[WifiLinkRecord] | ErrorPayload | None = None

    model_config = ConfigDict(extra="allow")
```

JSON wire format is preserved natively by Pydantic — `ErrorPayload` serializes to `{"error": "..."}` and validates from the same shape. No custom `model_serializer`/`model_validator` required.

### 10. `mcp_server.py` changes

- Tool surface unchanged. Same six named tools with their LLM-tuned docstrings.
- Tool bodies stay essentially as-is (calling client shims).
- The `get_all_datasets` MCP tool's docstring example is updated to show `is_ok(field)` / `field.error` for Python consumers. The JSON example for LLM consumers is unchanged.
- `mcp_server.py:545`'s `default_granularity="1s"` is unchanged.

## Backwards compatibility

| Surface | Change |
|---|---|
| Client public method names and signatures | None |
| `poll_dataset` accepted dataset names | None (alias table built to match exactly) |
| `poll_dataset` callback args (dataset name, records) | None — original string preserved verbatim |
| MCP tool surface and tool descriptions | None |
| JSON wire format of `AllDatasetsResponse` | None — Pydantic serializes `ErrorPayload` to `{"error": "..."}` natively |
| `AllDatasetsResponse` Python field types: error branch | **Breaking** — `dict` → `ErrorPayload` model |
| `AllDatasetsResponse` Python field types: success branch | None — still `list[X]`; `len()`, iteration, indexing all still work |
| `AllDatasetsResponse(... = {"error": "..."})` constructor input | Compatible — Pydantic union accepts the dict and coerces to `ErrorPayload` |
| `_get_dataset`, HTTP behavior, headers, timeouts | None |

The only Python-side breakage is reading the error branch: `field["error"]` becomes `field.error`, and `isinstance(field, dict)` becomes `isinstance(field, ErrorPayload)`. The tests at `test_models.py:858-861` and `test_client.py:566-570` are the known affected sites and will be updated as part of this change.

## Testing

### New tests

- `tests/test_datasets.py` (new file):
  - `DatasetSpec.wire_name()` for all five families across granularities (and override case).
  - `DatasetSpec.response_field()` for all five families across granularities.
  - `POLL_ALIASES` keys match the 9 wire names accepted by today's `poll_dataset` (golden assertion: full set of valid aliases, regression-proofed).
  - `parse_poll_alias` raises `ValueError` for unknown names with a helpful message.

- `tests/test_models.py` additions:
  - `ErrorPayload.of(exc)` constructs from an exception.
  - `is_ok(records)` / `is_ok(error_payload)`.
  - `unwrap(records)` returns the list; `unwrap(error_payload)` raises.
  - Round-trip serialization of `AllDatasetsResponse`: success field → bare JSON list → success field; error field → `{"error": "..."}` → `ErrorPayload`.

### Modified tests

- `tests/test_client.py`:
  - The six per-dataset success-path tests collapse into one parametrized test driven by `DATASETS`. Per-shim signature smoke tests stay (one per public method, asserting params are validated).
  - `test_get_all_datasets_with_error` (around line 566) switches from `isinstance(field, dict) and "error" in field` to `isinstance(field, ErrorPayload)` and `field.error == "Connection error"`.
  - `poll_dataset` tests cover at least one granular family and one non-granular family (especially `web_responsiveness_results` to confirm the alias is preserved). Callback assertion: callback receives the wire-alias string verbatim.

- `tests/test_models.py`:
  - `test_response_with_error` (around line 848) switches dict assertions to `ErrorPayload` assertions.
  - `test_valid_all_datasets_response` (around line 822) is unchanged — success-branch assertions on `list`, `len`, iteration all still pass.

### Acceptance criteria

- `uv run pytest tests/ -q` passes.
- Adding a hypothetical new dataset is a one-line addition to `DATASETS` plus a corresponding public shim and `AllDatasetsResponse` field; no `poll_dataset` or `get_all_datasets` edit required.
- `git grep '\[ScoreRecord\|\[ResponsivenessRecord\|\[WebResponsivenessRecord\|\[SpeedRecord\|\[WifiLinkRecord' src/orbnet/client.py` returns nothing — record-class instantiation lives only in `_fetch`.
- `git grep "isinstance.*dict.*error" src/orbnet tests/` returns nothing.
- `git grep '"error":' src/orbnet/` shows only the `ErrorPayload` definition (the dict literal at `client.py:594` is gone).

## File-by-file summary

| File | Change |
|---|---|
| `src/orbnet/datasets.py` | New: `DatasetSpec`, `DATASETS`, `POLL_ALIASES`, `parse_poll_alias`. |
| `src/orbnet/models.py` | Add `ErrorPayload`, `DatasetResult` TypeAlias, `is_ok`, `unwrap`. Replace `List[X] \| dict` field types in `AllDatasetsResponse` with `list[X] \| ErrorPayload`. |
| `src/orbnet/client.py` | Add private `_fetch`. Public methods become shims. `get_all_datasets` rewritten over the registry. `poll_dataset` rewritten over `parse_poll_alias`. Hard-coded `dataset_methods` dict removed. |
| `src/orbnet/mcp_server.py` | Update `get_all_datasets` MCP tool docstring example for Python consumers. No surface change. |
| `tests/test_datasets.py` | New file. |
| `tests/test_client.py` | Parametrize per-dataset success tests; update error-shape assertions. |
| `tests/test_models.py` | Add `ErrorPayload`/`is_ok`/`unwrap` tests; update error-branch assertions. |
