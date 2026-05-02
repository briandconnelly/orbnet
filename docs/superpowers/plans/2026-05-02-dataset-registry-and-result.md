# Dataset Registry and Result Type — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **User preference:** This user prefers to review commit messages before committing. Pause and surface the proposed commit message before running `git commit` in any task.

**Goal:** Replace the three parallel listings of dataset metadata (the five public dataset-fetching methods on `OrbAPIClient`, `poll_dataset`'s hardcoded dict, and `get_all_datasets`'s task dict) with a single registry in `src/orbnet/datasets.py`, and replace the `List[X] | dict` partial-failure leak in `AllDatasetsResponse` with a typed `ErrorPayload` + `DatasetResult` TypeAlias.

**Architecture:** A new `src/orbnet/datasets.py` becomes the single source of truth for dataset metadata. A private `_fetch(spec, granularity, caller_id, **params)` on `OrbAPIClient` is the one place that maps raw dicts to record classes. Public client methods become thin shims that validate inputs via the existing `<X>RequestParams` Pydantic models, then delegate. `get_all_datasets` and `poll_dataset` are rewritten to iterate the registry. `AllDatasetsResponse` fields gain `ErrorPayload` in their union; JSON wire format is preserved natively by Pydantic.

**Tech Stack:** Python 3.11+, Pydantic v2, httpx, FastMCP, pytest with `asyncio_mode = "auto"`. Package management via `uv`. Lint/format via `uv run --with ruff ruff ...`.

**Spec:** `docs/superpowers/specs/2026-05-02-dataset-registry-and-result-design.md`

---

## File structure

| File | Status | Responsibility |
|---|---|---|
| `src/orbnet/datasets.py` | Create | `DatasetSpec` dataclass, `DATASETS` registry, `POLL_ALIASES`, `parse_poll_alias`. Single source of truth for dataset metadata. |
| `src/orbnet/models.py` | Modify | Add `ErrorPayload`, `DatasetResult` TypeAlias, `is_ok`, `unwrap`. Replace `List[X] \| dict` field types in `AllDatasetsResponse` with `list[X] \| ErrorPayload`. |
| `src/orbnet/client.py` | Modify | Add private `_fetch`. Public methods become shims. Rewrite `get_all_datasets` over the registry. Rewrite `poll_dataset` over `parse_poll_alias`. Remove the hard-coded `dataset_methods` dict. |
| `src/orbnet/mcp_server.py` | Modify | Update `get_all_datasets` MCP tool docstring example to show `is_ok`/`field.error` for Python consumers. |
| `tests/test_datasets.py` | Create | Tests for `DatasetSpec`, registry shape, `POLL_ALIASES`, `parse_poll_alias`. |
| `tests/test_models.py` | Modify | Add `ErrorPayload`/`is_ok`/`unwrap` tests. Update error-branch assertions on `AllDatasetsResponse`. |
| `tests/test_client.py` | Modify | Update error-shape assertions in `test_get_all_datasets_with_error`. Parametrize per-dataset success tests over `DATASETS`. Add `poll_dataset` test asserting callback receives the wire-alias verbatim. |

---

## Task 1: Set up feature branch

**Files:**
- Modify: working tree only

- [ ] **Step 1: Confirm working tree is clean**

Run: `git status`
Expected: clean tree (no staged or unstaged changes; the existing `.claude/` and `coverage.xml` untracked entries are fine).

- [ ] **Step 2: Create and check out feature branch from `main`**

Run: `git checkout -b dataset-registry-and-result`
Expected: `Switched to a new branch 'dataset-registry-and-result'`

- [ ] **Step 3: Verify branch**

Run: `git branch --show-current`
Expected: `dataset-registry-and-result`

---

## Task 2: Add `ErrorPayload`, `DatasetResult`, `is_ok`, `unwrap` in `models.py`

These are additive — no callers wired up yet.

**Files:**
- Modify: `src/orbnet/models.py` (add new types after existing imports and before `AllDatasetsResponse`)
- Test: `tests/test_models.py`

- [ ] **Step 1: Write failing tests for `ErrorPayload`, `is_ok`, `unwrap`**

Append to the end of `tests/test_models.py`:

```python
class TestErrorPayload:
    """Test ErrorPayload model and is_ok/unwrap helpers."""

    def test_error_payload_basic(self):
        from orbnet.models import ErrorPayload

        payload = ErrorPayload(error="boom")
        assert payload.error == "boom"

    def test_error_payload_of_exception(self):
        from orbnet.models import ErrorPayload

        payload = ErrorPayload.of(ValueError("kaboom"))
        assert payload.error == "kaboom"

    def test_error_payload_serialization(self):
        from orbnet.models import ErrorPayload

        payload = ErrorPayload(error="boom")
        assert payload.model_dump() == {"error": "boom"}

    def test_error_payload_validates_from_dict(self):
        from orbnet.models import ErrorPayload

        payload = ErrorPayload.model_validate({"error": "boom"})
        assert payload.error == "boom"

    def test_is_ok_with_list(self):
        from orbnet.models import is_ok

        assert is_ok([]) is True
        assert is_ok([1, 2, 3]) is True

    def test_is_ok_with_error_payload(self):
        from orbnet.models import ErrorPayload, is_ok

        assert is_ok(ErrorPayload(error="boom")) is False

    def test_unwrap_returns_list_when_ok(self):
        from orbnet.models import unwrap

        assert unwrap([1, 2, 3]) == [1, 2, 3]

    def test_unwrap_raises_on_error_payload(self):
        from orbnet.models import ErrorPayload, unwrap

        with pytest.raises(ValueError, match="Dataset failed: boom"):
            unwrap(ErrorPayload(error="boom"))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_models.py::TestErrorPayload -v`
Expected: FAIL — `ImportError` or `AttributeError` for `ErrorPayload`/`is_ok`/`unwrap`.

- [ ] **Step 3: Add `ErrorPayload`, `DatasetResult`, `is_ok`, `unwrap` to `models.py`**

In `src/orbnet/models.py`, ensure the imports include `TypeAlias` and `TypeVar` (Python 3.11+ has `TypeAlias` in `typing`):

```python
from typing import Any, Generic, List, Literal, Optional, TypeAlias, TypeVar
```

(Update this line to include `TypeAlias, TypeVar` — keep existing imports.)

Then add the following block immediately above the `AllDatasetsResponse` class definition (currently around line 454):

```python
# ============================================================================
# Result type for partial-failure batch responses
# ============================================================================


class ErrorPayload(BaseModel):
    """Typed error payload used in AllDatasetsResponse fields when a dataset fetch fails.

    Serializes to {"error": "..."} and validates from the same shape, preserving
    the JSON wire format that previously used a bare dict.
    """

    error: str

    model_config = ConfigDict(extra="forbid")

    @classmethod
    def of(cls, exc: BaseException) -> "ErrorPayload":
        return cls(error=str(exc))


T = TypeVar("T")

DatasetResult: TypeAlias = list[T] | ErrorPayload


def is_ok(value: list | ErrorPayload) -> bool:
    """Return True iff `value` is a successful dataset result (a list)."""
    return not isinstance(value, ErrorPayload)


def unwrap(value: list[T] | ErrorPayload) -> list[T]:
    """Return the list when `value` is ok, else raise ValueError."""
    if isinstance(value, ErrorPayload):
        raise ValueError(f"Dataset failed: {value.error}")
    return value
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_models.py::TestErrorPayload -v`
Expected: all 8 tests PASS.

- [ ] **Step 5: Run the full test suite to verify no regressions**

Run: `uv run pytest tests/ -q`
Expected: all tests pass (89 + 8 = 97 expected).

- [ ] **Step 6: Commit**

Pause and surface this proposed commit message to the user; wait for approval.

```bash
git add src/orbnet/models.py tests/test_models.py
git commit -m "feat(models): add ErrorPayload, DatasetResult, is_ok, unwrap

Introduce a typed error payload alongside list-based success values, plus
helpers for narrowing the union. Not yet wired into AllDatasetsResponse;
that change comes in the next commit. Pure additions — no behavior change."
```

---

## Task 3: Wire `ErrorPayload` into `AllDatasetsResponse` field types

This is the breaking-change moment for the Python error-branch type. JSON wire format is preserved.

**Files:**
- Modify: `src/orbnet/models.py:454-472` (the `AllDatasetsResponse` class)
- Modify: `src/orbnet/client.py:591-596` (the dict-construction in `get_all_datasets`)
- Modify: `tests/test_models.py` (one assertion update around line 858)
- Modify: `tests/test_client.py` (one assertion update around line 568)

- [ ] **Step 1: Update `AllDatasetsResponse` field types**

In `src/orbnet/models.py`, replace the body of `AllDatasetsResponse` (the field declarations only — keep `model_config = ConfigDict(extra="allow")`):

```python
class AllDatasetsResponse(BaseModel):
    """
    Response containing all datasets.

    Each dataset field contains either a list of records or an ErrorPayload
    (typed `{"error": "..."}` payload) if that dataset failed to fetch.
    """

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

- [ ] **Step 2: Update `get_all_datasets` to construct `ErrorPayload` instead of bare dicts**

In `src/orbnet/client.py`, locate the dict comprehension at lines 591–596:

```python
result_dict = {
    key: result
    if not isinstance(result, BaseException)
    else {"error": str(result)}
    for key, result in zip(tasks.keys(), results, strict=True)
}
```

Replace with:

```python
result_dict = {
    key: result
    if not isinstance(result, BaseException)
    else ErrorPayload.of(result)
    for key, result in zip(tasks.keys(), results, strict=True)
}
```

Add `ErrorPayload` to the imports at the top of `client.py`:

```python
from .models import (
    AllDatasetsRequestParams,
    AllDatasetsResponse,
    DatasetRequestParams,
    ErrorPayload,
    OrbClientConfig,
    PollingConfig,
    ResponsivenessRecord,
    ResponsivenessRequestParams,
    ScoreRecord,
    SpeedRecord,
    WebResponsivenessRecord,
    WifiLinkRecord,
)
```

(Insert `ErrorPayload` alphabetically — between `DatasetRequestParams` and `OrbClientConfig`.)

- [ ] **Step 3: Update `tests/test_models.py::test_response_with_error` assertions**

Around `tests/test_models.py:858-861`, replace:

```python
        assert isinstance(response.scores_1m, list)
        assert isinstance(response.responsiveness_1m, dict)
        assert "error" in response.responsiveness_1m
        assert response.responsiveness_1m["error"] == "Connection timeout"
```

With:

```python
        from orbnet.models import ErrorPayload

        assert isinstance(response.scores_1m, list)
        assert isinstance(response.responsiveness_1m, ErrorPayload)
        assert response.responsiveness_1m.error == "Connection timeout"
```

- [ ] **Step 4: Update `tests/test_client.py::test_get_all_datasets_with_error` assertions**

Around `tests/test_client.py:566-572`, replace:

```python
            assert isinstance(result, AllDatasetsResponse)
            assert isinstance(result.scores_1m, list)
            assert isinstance(result.responsiveness_1m, dict)
            assert "error" in result.responsiveness_1m
            assert result.responsiveness_1m["error"] == "Connection error"
            assert isinstance(result.web_responsiveness, list)
            assert isinstance(result.speed_results, list)
```

With:

```python
            from orbnet.models import ErrorPayload

            assert isinstance(result, AllDatasetsResponse)
            assert isinstance(result.scores_1m, list)
            assert isinstance(result.responsiveness_1m, ErrorPayload)
            assert result.responsiveness_1m.error == "Connection error"
            assert isinstance(result.web_responsiveness, list)
            assert isinstance(result.speed_results, list)
```

- [ ] **Step 5: Add a JSON round-trip test for the wire format**

Append to the end of `tests/test_models.py`:

```python
class TestAllDatasetsResponseWireFormat:
    """Verify that AllDatasetsResponse preserves the JSON wire format."""

    def test_error_field_serializes_to_error_dict(
        self, sample_scores_data, sample_wifi_link_data
    ):
        from orbnet.models import ErrorPayload

        response = AllDatasetsResponse(
            scores_1m=[ScoreRecord(**r) for r in sample_scores_data],
            responsiveness_1m=ErrorPayload(error="boom"),
            web_responsiveness=[],
            speed_results=[],
            wifi_link_1m=[WifiLinkRecord(**r) for r in sample_wifi_link_data],
        )
        dumped = response.model_dump()
        assert dumped["responsiveness_1m"] == {"error": "boom"}

    def test_error_field_validates_from_error_dict(
        self, sample_scores_data, sample_wifi_link_data
    ):
        from orbnet.models import ErrorPayload

        response = AllDatasetsResponse(
            scores_1m=[ScoreRecord(**r) for r in sample_scores_data],
            responsiveness_1m={"error": "boom"},
            web_responsiveness=[],
            speed_results=[],
            wifi_link_1m=[WifiLinkRecord(**r) for r in sample_wifi_link_data],
        )
        assert isinstance(response.responsiveness_1m, ErrorPayload)
        assert response.responsiveness_1m.error == "boom"
```

- [ ] **Step 6: Run the full test suite**

Run: `uv run pytest tests/ -q`
Expected: all tests pass.

- [ ] **Step 7: Commit**

Pause and surface this proposed commit message to the user; wait for approval.

```bash
git add src/orbnet/models.py src/orbnet/client.py tests/test_models.py tests/test_client.py
git commit -m "refactor(models): replace List[X]|dict union with ErrorPayload in AllDatasetsResponse

JSON wire format unchanged (Pydantic serializes ErrorPayload to {\"error\": ...}
and validates from the same shape). Python-side error branch becomes a typed
model: tests update field['error'] -> field.error and isinstance(field, dict)
-> isinstance(field, ErrorPayload). Success branch (list) is unchanged."
```

---

## Task 4: Create `src/orbnet/datasets.py` with `DatasetSpec`

**Files:**
- Create: `src/orbnet/datasets.py`
- Test: `tests/test_datasets.py`

- [ ] **Step 1: Write failing tests for `DatasetSpec`**

Create `tests/test_datasets.py` with:

```python
"""Tests for orbnet.datasets — DatasetSpec, DATASETS registry, POLL_ALIASES."""

import pytest

from orbnet.datasets import DatasetSpec
from orbnet.models import (
    ResponsivenessRecord,
    ScoreRecord,
    SpeedRecord,
    WebResponsivenessRecord,
    WifiLinkRecord,
)


class TestDatasetSpec:
    def test_non_granular_wire_name(self):
        spec = DatasetSpec(family="speed_results", record_class=SpeedRecord)
        assert spec.wire_name() == "speed_results"

    def test_non_granular_response_field(self):
        spec = DatasetSpec(family="speed_results", record_class=SpeedRecord)
        assert spec.response_field() == "speed_results"

    def test_granular_wire_name_explicit_granularity(self):
        spec = DatasetSpec(
            family="responsiveness",
            record_class=ResponsivenessRecord,
            granularities=("1s", "15s", "1m"),
            default_granularity="1m",
        )
        assert spec.wire_name("1s") == "responsiveness_1s"
        assert spec.wire_name("15s") == "responsiveness_15s"
        assert spec.wire_name("1m") == "responsiveness_1m"

    def test_granular_wire_name_uses_default(self):
        spec = DatasetSpec(
            family="responsiveness",
            record_class=ResponsivenessRecord,
            granularities=("1s", "15s", "1m"),
            default_granularity="1m",
        )
        assert spec.wire_name() == "responsiveness_1m"

    def test_granular_response_field(self):
        spec = DatasetSpec(
            family="responsiveness",
            record_class=ResponsivenessRecord,
            granularities=("1s", "15s", "1m"),
            default_granularity="1m",
        )
        assert spec.response_field("1s") == "responsiveness_1s"
        assert spec.response_field() == "responsiveness_1m"

    def test_wire_name_override(self):
        spec = DatasetSpec(
            family="web_responsiveness",
            record_class=WebResponsivenessRecord,
            wire_name_override="web_responsiveness_results",
        )
        assert spec.wire_name() == "web_responsiveness_results"

    def test_response_field_unaffected_by_wire_name_override(self):
        """Field name must NOT inherit the override; AllDatasetsResponse uses
        `web_responsiveness`, not `web_responsiveness_results`."""
        spec = DatasetSpec(
            family="web_responsiveness",
            record_class=WebResponsivenessRecord,
            wire_name_override="web_responsiveness_results",
        )
        assert spec.response_field() == "web_responsiveness"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_datasets.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'orbnet.datasets'`.

- [ ] **Step 3: Create `src/orbnet/datasets.py` with `DatasetSpec`**

```python
"""Single source of truth for dataset metadata.

Each entry in DATASETS captures everything callers need to know about a
dataset family: which Pydantic record class its rows decode to, what
granularities it supports, and how its name is rendered on the wire and
in AllDatasetsResponse.
"""

from dataclasses import dataclass

from .models import BaseRecord


@dataclass(frozen=True)
class DatasetSpec:
    """Metadata describing one dataset family.

    Three name spaces are tracked:

    - `family`: the registry key — also the public-method root (`get_<family>`).
    - `wire_name(granularity)`: the URL-path component used by the Orb API.
      Equals `family` for non-granular datasets, `f"{family}_{granularity}"`
      for granular ones, or `wire_name_override` when set.
    - `response_field(granularity)`: which `AllDatasetsResponse` slot this
      result populates. Equals `family` for non-granular datasets and
      `f"{family}_{granularity}"` for granular ones. Never inherits the
      wire-name override (e.g. `web_responsiveness` field, `web_responsiveness_results` wire).
    """

    family: str
    record_class: type[BaseRecord]
    granularities: tuple[str, ...] = ()
    default_granularity: str | None = None
    wire_name_override: str | None = None

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

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_datasets.py -v`
Expected: all 7 `TestDatasetSpec` tests PASS.

- [ ] **Step 5: Commit**

Pause and surface this proposed commit message to the user; wait for approval.

```bash
git add src/orbnet/datasets.py tests/test_datasets.py
git commit -m "feat(datasets): add DatasetSpec dataclass

New module that will host the dataset registry. DatasetSpec tracks the three
name spaces (family, wire name, response field) explicitly — wire_name_override
exists for web_responsiveness, where the wire path has a _results suffix that
the response field does not."
```

---

## Task 5: Add `DATASETS` registry to `datasets.py`

**Files:**
- Modify: `src/orbnet/datasets.py`
- Modify: `tests/test_datasets.py`

- [ ] **Step 1: Write failing tests for the registry**

Append to `tests/test_datasets.py`:

```python
class TestDatasetsRegistry:
    """Verify the registry has exactly the five expected families with correct shapes."""

    def test_registry_has_five_families(self):
        from orbnet.datasets import DATASETS

        assert set(DATASETS.keys()) == {
            "scores",
            "responsiveness",
            "web_responsiveness",
            "speed_results",
            "wifi_link",
        }

    def test_scores_family(self):
        from orbnet.datasets import DATASETS

        spec = DATASETS["scores"]
        assert spec.record_class is ScoreRecord
        assert spec.granularities == ("1m",)
        assert spec.default_granularity == "1m"
        assert spec.wire_name() == "scores_1m"
        assert spec.response_field() == "scores_1m"

    def test_responsiveness_family(self):
        from orbnet.datasets import DATASETS

        spec = DATASETS["responsiveness"]
        assert spec.record_class is ResponsivenessRecord
        assert spec.granularities == ("1s", "15s", "1m")
        assert spec.default_granularity == "1m"
        assert spec.wire_name("1s") == "responsiveness_1s"

    def test_web_responsiveness_family(self):
        from orbnet.datasets import DATASETS

        spec = DATASETS["web_responsiveness"]
        assert spec.record_class is WebResponsivenessRecord
        assert spec.granularities == ()
        assert spec.wire_name() == "web_responsiveness_results"
        assert spec.response_field() == "web_responsiveness"

    def test_speed_results_family(self):
        from orbnet.datasets import DATASETS

        spec = DATASETS["speed_results"]
        assert spec.record_class is SpeedRecord
        assert spec.granularities == ()
        assert spec.wire_name() == "speed_results"

    def test_wifi_link_family(self):
        from orbnet.datasets import DATASETS

        spec = DATASETS["wifi_link"]
        assert spec.record_class is WifiLinkRecord
        assert spec.granularities == ("1s", "15s", "1m")
        assert spec.default_granularity == "1m"
        assert spec.wire_name("15s") == "wifi_link_15s"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_datasets.py::TestDatasetsRegistry -v`
Expected: FAIL — `ImportError` for `DATASETS`.

- [ ] **Step 3: Add `DATASETS` to `src/orbnet/datasets.py`**

Update the imports at the top of `src/orbnet/datasets.py`:

```python
from dataclasses import dataclass

from .models import (
    BaseRecord,
    ResponsivenessRecord,
    ScoreRecord,
    SpeedRecord,
    WebResponsivenessRecord,
    WifiLinkRecord,
)
```

Append to the bottom of `src/orbnet/datasets.py`:

```python
DATASETS: dict[str, DatasetSpec] = {
    "scores": DatasetSpec(
        family="scores",
        record_class=ScoreRecord,
        granularities=("1m",),
        default_granularity="1m",
    ),
    "responsiveness": DatasetSpec(
        family="responsiveness",
        record_class=ResponsivenessRecord,
        granularities=("1s", "15s", "1m"),
        default_granularity="1m",
    ),
    "web_responsiveness": DatasetSpec(
        family="web_responsiveness",
        record_class=WebResponsivenessRecord,
        wire_name_override="web_responsiveness_results",
    ),
    "speed_results": DatasetSpec(
        family="speed_results",
        record_class=SpeedRecord,
    ),
    "wifi_link": DatasetSpec(
        family="wifi_link",
        record_class=WifiLinkRecord,
        granularities=("1s", "15s", "1m"),
        default_granularity="1m",
    ),
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_datasets.py -v`
Expected: all tests PASS (7 TestDatasetSpec + 6 TestDatasetsRegistry).

- [ ] **Step 5: Commit**

Pause and surface this proposed commit message to the user; wait for approval.

```bash
git add src/orbnet/datasets.py tests/test_datasets.py
git commit -m "feat(datasets): add DATASETS registry with five families

Single source of truth for which datasets exist, what they return, and which
granularities they support. Not yet consumed by client.py — that comes next."
```

---

## Task 6: Add `POLL_ALIASES` and `parse_poll_alias`

**Files:**
- Modify: `src/orbnet/datasets.py`
- Modify: `tests/test_datasets.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_datasets.py`:

```python
class TestPollAliases:
    """POLL_ALIASES must accept exactly the wire names today's poll_dataset accepts."""

    EXPECTED_ALIASES = {
        "scores_1m",
        "responsiveness_1s",
        "responsiveness_15s",
        "responsiveness_1m",
        "web_responsiveness_results",
        "speed_results",
        "wifi_link_1s",
        "wifi_link_15s",
        "wifi_link_1m",
    }

    def test_aliases_match_today_exactly(self):
        from orbnet.datasets import POLL_ALIASES

        assert set(POLL_ALIASES.keys()) == self.EXPECTED_ALIASES

    def test_parse_poll_alias_granular(self):
        from orbnet.datasets import DATASETS, parse_poll_alias

        spec, granularity = parse_poll_alias("responsiveness_1s")
        assert spec is DATASETS["responsiveness"]
        assert granularity == "1s"

    def test_parse_poll_alias_non_granular(self):
        from orbnet.datasets import DATASETS, parse_poll_alias

        spec, granularity = parse_poll_alias("speed_results")
        assert spec is DATASETS["speed_results"]
        assert granularity is None

    def test_parse_poll_alias_web_responsiveness_with_override(self):
        from orbnet.datasets import DATASETS, parse_poll_alias

        spec, granularity = parse_poll_alias("web_responsiveness_results")
        assert spec is DATASETS["web_responsiveness"]
        assert granularity is None

    def test_parse_poll_alias_unknown_raises_with_message(self):
        from orbnet.datasets import parse_poll_alias

        with pytest.raises(ValueError, match="Unknown dataset: bogus"):
            parse_poll_alias("bogus")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_datasets.py::TestPollAliases -v`
Expected: FAIL — `ImportError` for `POLL_ALIASES`/`parse_poll_alias`.

- [ ] **Step 3: Add `POLL_ALIASES` and `parse_poll_alias` to `datasets.py`**

Append to `src/orbnet/datasets.py`:

```python
def _build_poll_aliases(
    datasets: dict[str, DatasetSpec],
) -> dict[str, tuple[DatasetSpec, str | None]]:
    aliases: dict[str, tuple[DatasetSpec, str | None]] = {}
    for spec in datasets.values():
        if spec.granularities:
            for g in spec.granularities:
                aliases[spec.wire_name(g)] = (spec, g)
        else:
            aliases[spec.wire_name()] = (spec, None)
    return aliases


POLL_ALIASES: dict[str, tuple[DatasetSpec, str | None]] = _build_poll_aliases(DATASETS)


def parse_poll_alias(name: str) -> tuple[DatasetSpec, str | None]:
    """Resolve a wire-name string (as accepted by poll_dataset) to (spec, granularity).

    Raises ValueError with the list of valid options if `name` is unknown.
    """
    if name not in POLL_ALIASES:
        raise ValueError(
            f"Unknown dataset: {name}. Valid options: {', '.join(sorted(POLL_ALIASES))}"
        )
    return POLL_ALIASES[name]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_datasets.py -v`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

Pause and surface this proposed commit message; wait for approval.

```bash
git add src/orbnet/datasets.py tests/test_datasets.py
git commit -m "feat(datasets): add POLL_ALIASES table and parse_poll_alias()

Built once from the registry; aliases match today's poll_dataset accepted
inputs exactly, including web_responsiveness_results."
```

---

## Task 7: Add private `_fetch` helper to `OrbAPIClient`

**Files:**
- Modify: `src/orbnet/client.py` (add `_fetch` after `_get_dataset`)
- Modify: `tests/test_client.py` (add a unit test class for `_fetch`)

- [ ] **Step 1: Write a failing test for `_fetch`**

Append to `tests/test_client.py` (above any existing class footer if present, or at the end of the file):

```python
class TestFetchHelper:
    """Direct tests for the private _fetch helper on OrbAPIClient."""

    @pytest.mark.asyncio
    async def test_fetch_passes_wire_name_and_maps_records(
        self, sample_scores_data, mock_httpx_response
    ):
        from orbnet.datasets import DATASETS

        mock_httpx_response.json.return_value = sample_scores_data

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_httpx_response

            client = OrbAPIClient(host="192.168.1.100")
            result = await client._fetch(DATASETS["scores"], "1m")

            assert mock_client.get.called
            url = mock_client.get.call_args[0][0]
            assert "scores_1m.json" in url

            assert all(isinstance(r, ScoreRecord) for r in result)
            assert len(result) == len(sample_scores_data)

    @pytest.mark.asyncio
    async def test_fetch_uses_default_granularity_when_omitted(
        self, sample_responsiveness_data, mock_httpx_response
    ):
        from orbnet.datasets import DATASETS

        mock_httpx_response.json.return_value = sample_responsiveness_data

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_httpx_response

            client = OrbAPIClient(host="192.168.1.100")
            await client._fetch(DATASETS["responsiveness"])

            url = mock_client.get.call_args[0][0]
            assert "responsiveness_1m.json" in url

    @pytest.mark.asyncio
    async def test_fetch_honors_wire_name_override(
        self, sample_web_responsiveness_data, mock_httpx_response
    ):
        from orbnet.datasets import DATASETS

        mock_httpx_response.json.return_value = sample_web_responsiveness_data

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_httpx_response

            client = OrbAPIClient(host="192.168.1.100")
            await client._fetch(DATASETS["web_responsiveness"])

            url = mock_client.get.call_args[0][0]
            assert "web_responsiveness_results.json" in url
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_client.py::TestFetchHelper -v`
Expected: FAIL — `AttributeError: 'OrbAPIClient' object has no attribute '_fetch'`.

- [ ] **Step 3: Add `_fetch` to `OrbAPIClient`**

In `src/orbnet/client.py`, add this method immediately after `_get_dataset` (around line 168). Also add `DatasetSpec` to the imports from `.datasets`:

```python
from .datasets import DatasetSpec
```

(Place this import below the `from .models import ...` block.)

Then the new method:

```python
    async def _fetch(
        self,
        spec: "DatasetSpec",
        granularity: Optional[str] = None,
        caller_id: Optional[str] = None,
        **params,
    ) -> List[Any]:
        """Fetch one dataset and map records to spec.record_class.

        Internal helper. The single place that turns raw JSON dicts into
        Pydantic record instances. Public methods (get_scores_1m, etc.) are
        thin shims over this. `granularity` is honored only for granular
        families; ignored otherwise. Validation of the granularity string
        is the caller's responsibility (see public-method shims).
        """
        raw_data = await self._get_dataset(
            spec.wire_name(granularity),
            caller_id=caller_id,
            **params,
        )
        return [spec.record_class(**record) for record in raw_data]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_client.py::TestFetchHelper -v`
Expected: all 3 tests PASS.

- [ ] **Step 5: Run full test suite**

Run: `uv run pytest tests/ -q`
Expected: all tests pass.

- [ ] **Step 6: Commit**

Pause and surface this proposed commit message; wait for approval.

```bash
git add src/orbnet/client.py tests/test_client.py
git commit -m "feat(client): add private _fetch helper

Single place for raw-dict to record-class mapping. Will be the body of the
public method shims in the next commit."
```

---

## Task 8: Convert public client methods to shims over `_fetch`

The five public dataset-fetching methods become 1-3 line bodies. Existing tests must remain green.

**Files:**
- Modify: `src/orbnet/client.py:170-422` (six method bodies)

- [ ] **Step 1: Update imports at the top of `client.py`**

Ensure `DATASETS` is imported (you added `DatasetSpec` in Task 7 — extend that import):

```python
from .datasets import DATASETS, DatasetSpec
```

- [ ] **Step 2: Replace `get_scores_1m` body**

Locate `get_scores_1m` (around line 170). Replace ONLY the function body (keep the signature and docstring); the new body is:

```python
        request = DatasetRequestParams(caller_id=caller_id, **params)
        return await self._fetch(
            DATASETS["scores"],
            "1m",
            caller_id=request.caller_id,
            **params,
        )
```

- [ ] **Step 3: Replace `get_responsiveness` body**

Locate `get_responsiveness` (around line 233). Replace the body with:

```python
        request = ResponsivenessRequestParams(
            granularity=granularity, caller_id=caller_id, **params
        )
        return await self._fetch(
            DATASETS["responsiveness"],
            request.granularity,
            caller_id=request.caller_id,
            **params,
        )
```

- [ ] **Step 4: Replace `get_web_responsiveness` body**

Locate `get_web_responsiveness` (around line 299). Replace the body with:

```python
        request = DatasetRequestParams(caller_id=caller_id, **params)
        return await self._fetch(
            DATASETS["web_responsiveness"],
            caller_id=request.caller_id,
            **params,
        )
```

- [ ] **Step 5: Replace `get_speed_results` body**

Locate `get_speed_results` (around line 365). Replace the body with:

```python
        request = DatasetRequestParams(caller_id=caller_id, **params)
        return await self._fetch(
            DATASETS["speed_results"],
            caller_id=request.caller_id,
            **params,
        )
```

- [ ] **Step 6: Replace `get_wifi_link` body**

Locate `get_wifi_link` (the file currently has it after `get_speed_results`). Replace the body with:

```python
        request = ResponsivenessRequestParams(
            granularity=granularity, caller_id=caller_id, **params
        )
        return await self._fetch(
            DATASETS["wifi_link"],
            request.granularity,
            caller_id=request.caller_id,
            **params,
        )
```

(Note: `get_wifi_link` reuses `ResponsivenessRequestParams` for granularity validation today — preserve that.)

- [ ] **Step 7: Run the full test suite — existing tests must still pass**

Run: `uv run pytest tests/ -q`
Expected: all tests pass with no behavior change.

- [ ] **Step 8: Verify the per-record-class instantiation has been removed from public methods**

Run: `git diff src/orbnet/client.py | grep -E '^\+.*\[(ScoreRecord|ResponsivenessRecord|WebResponsivenessRecord|SpeedRecord|WifiLinkRecord)\(\*\*'`
Expected: no output (the only `[X(**r) for r in ...]` patterns left are inside `_fetch`).

- [ ] **Step 9: Commit**

Pause and surface this proposed commit message; wait for approval.

```bash
git add src/orbnet/client.py
git commit -m "refactor(client): collapse public methods to shims over _fetch

Public signatures and docstrings unchanged. Per-method validation via
<X>RequestParams Pydantic models is preserved. All record-class
instantiation now lives in _fetch."
```

---

## Task 9: Rewrite `get_all_datasets` over the registry

**Files:**
- Modify: `src/orbnet/client.py` (the `get_all_datasets` method, around lines 480-598)

- [ ] **Step 1: Replace `get_all_datasets` implementation**

Locate `get_all_datasets`. The method's docstring and signature stay; replace ONLY the function body (everything after the closing `"""` of the docstring) with:

```python
        request = AllDatasetsRequestParams(
            caller_id=caller_id,
            include_all_responsiveness=include_all_responsiveness,
            include_all_wifi_link=include_all_wifi_link,
        )

        include_all_map = {
            "responsiveness": request.include_all_responsiveness,
            "wifi_link": request.include_all_wifi_link,
        }

        plan: list[tuple[DatasetSpec, Optional[str]]] = []
        for spec in DATASETS.values():
            if not spec.granularities:
                plan.append((spec, None))
                continue
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

        results = await asyncio.gather(
            *[self._fetch(spec, g, request.caller_id) for spec, g in plan],
            return_exceptions=True,
        )

        fields: dict[str, Any] = {}
        for (spec, g), result in zip(plan, results, strict=True):
            fields[spec.response_field(g)] = (
                ErrorPayload.of(result) if isinstance(result, BaseException) else result
            )
        return AllDatasetsResponse(**fields)
```

(The earlier `result_dict = {... {"error": str(result)} ...}` block from Task 3 is now superseded by this rewrite — its `ErrorPayload.of(result)` line ends up here instead.)

- [ ] **Step 2: Run the full test suite — existing tests must still pass**

Run: `uv run pytest tests/ -q`
Expected: all tests pass. The success-path tests (`test_get_all_datasets_basic`, etc.) cover this rewrite; the error-path test was updated in Task 3.

- [ ] **Step 3: Manual sanity check on the plan logic**

Add a quick parametrized test in `tests/test_client.py` to lock the plan logic, just below `TestFetchHelper`:

```python
class TestGetAllDatasetsPlan:
    """Verify get_all_datasets dispatches to the right wire endpoints."""

    @pytest.mark.asyncio
    async def test_default_granularity_1s_populates_1s_fields(
        self,
        sample_scores_data,
        sample_responsiveness_data,
        sample_web_responsiveness_data,
        sample_speed_data,
        sample_wifi_link_data,
    ):
        # Map dataset wire-name -> raw response.
        responses = {
            "scores_1m": sample_scores_data,
            "responsiveness_1s": sample_responsiveness_data,
            "web_responsiveness_results": sample_web_responsiveness_data,
            "speed_results": sample_speed_data,
            "wifi_link_1s": sample_wifi_link_data,
        }

        async def fake_get_dataset(self, dataset_name, caller_id=None, **params):
            return responses[dataset_name]

        with patch.object(OrbAPIClient, "_get_dataset", new=fake_get_dataset):
            client = OrbAPIClient(host="192.168.1.100")
            result = await client.get_all_datasets(default_granularity="1s")

            assert isinstance(result.scores_1m, list) and len(result.scores_1m) > 0
            assert isinstance(result.responsiveness_1s, list)
            assert isinstance(result.wifi_link_1s, list)
            assert result.responsiveness_1m is None
            assert result.wifi_link_1m is None

    @pytest.mark.asyncio
    async def test_include_all_responsiveness_fetches_all_three(
        self,
        sample_scores_data,
        sample_responsiveness_data,
        sample_web_responsiveness_data,
        sample_speed_data,
        sample_wifi_link_data,
    ):
        responses = {
            "scores_1m": sample_scores_data,
            "responsiveness_1s": sample_responsiveness_data,
            "responsiveness_15s": sample_responsiveness_data,
            "responsiveness_1m": sample_responsiveness_data,
            "web_responsiveness_results": sample_web_responsiveness_data,
            "speed_results": sample_speed_data,
            "wifi_link_1m": sample_wifi_link_data,
        }

        async def fake_get_dataset(self, dataset_name, caller_id=None, **params):
            return responses[dataset_name]

        with patch.object(OrbAPIClient, "_get_dataset", new=fake_get_dataset):
            client = OrbAPIClient(host="192.168.1.100")
            result = await client.get_all_datasets(include_all_responsiveness=True)

            assert isinstance(result.responsiveness_1s, list)
            assert isinstance(result.responsiveness_15s, list)
            assert isinstance(result.responsiveness_1m, list)
            assert result.wifi_link_15s is None
            assert result.wifi_link_1s is None
```

- [ ] **Step 4: Run new tests to verify they pass**

Run: `uv run pytest tests/test_client.py::TestGetAllDatasetsPlan -v`
Expected: 2 tests PASS.

- [ ] **Step 5: Run the full test suite**

Run: `uv run pytest tests/ -q`
Expected: all tests pass.

- [ ] **Step 6: Commit**

Pause and surface this proposed commit message; wait for approval.

```bash
git add src/orbnet/client.py tests/test_client.py
git commit -m "refactor(client): drive get_all_datasets from the registry

Two-phase: build (spec, granularity) plan from the registry x caller's
default_granularity x include_all_* flags, then asyncio.gather and assemble
fields via spec.response_field(granularity). Behavior preserved; the only
family-name conditional is a localized include_all_map for the two
public flags whose names are baked into the function signature."
```

---

## Task 10: Rewrite `poll_dataset` over `parse_poll_alias`

**Files:**
- Modify: `src/orbnet/client.py` (the `poll_dataset` method, around lines 600-744)
- Modify: `tests/test_client.py` (add callback-verbatim test)

- [ ] **Step 1: Add a failing test for the callback verbatim contract**

Append to `tests/test_client.py`:

```python
class TestPollDatasetCallbackContract:
    """The user-supplied dataset_name string must reach callbacks unchanged.

    Today's callers expect 'web_responsiveness_results' (not 'web_responsiveness'
    or some other normalization) to flow through to their callback's first arg.
    """

    @pytest.mark.asyncio
    async def test_callback_receives_wire_alias_verbatim(
        self, sample_web_responsiveness_data, mock_httpx_response
    ):
        mock_httpx_response.json.return_value = sample_web_responsiveness_data

        captured: list[str] = []

        def callback(dataset_name, records):
            captured.append(dataset_name)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_httpx_response

            client = OrbAPIClient(host="192.168.1.100")
            async for _ in client.poll_dataset(
                "web_responsiveness_results",
                interval=0.01,
                callback=callback,
                max_iterations=1,
            ):
                pass

        assert captured == ["web_responsiveness_results"]
```

- [ ] **Step 2: Run test — should pass against current code**

Run: `uv run pytest tests/test_client.py::TestPollDatasetCallbackContract -v`
Expected: PASS (current code already does this; the test locks the contract before refactor).

- [ ] **Step 3: Replace `poll_dataset` body with the registry-driven version**

In `src/orbnet/client.py`, locate `poll_dataset`. Replace ONLY the function body (everything after the closing `"""` of the docstring) with:

```python
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

- [ ] **Step 4: Add `parse_poll_alias` to the `.datasets` import in `client.py`**

```python
from .datasets import DATASETS, DatasetSpec, parse_poll_alias
```

- [ ] **Step 5: Run full test suite**

Run: `uv run pytest tests/ -q`
Expected: all tests pass — including existing `poll_dataset` tests and the new callback-verbatim test.

- [ ] **Step 6: Commit**

Pause and surface this proposed commit message; wait for approval.

```bash
git add src/orbnet/client.py tests/test_client.py
git commit -m "refactor(client): drive poll_dataset from POLL_ALIASES

The hard-coded 9-entry dataset_methods dict is gone; validation routes
through parse_poll_alias. Accepted input space and callback contract
preserved exactly — the user-supplied dataset_name string is passed
verbatim to user callbacks (test added to lock that contract)."
```

---

## Task 11: Parametrize per-dataset success tests in `test_client.py`

The near-identical `test_get_<dataset>_success` tests (one per public dataset-fetching method) collapse into one parametrized test driven by `DATASETS`. Per-method signature smoke tests stay (one per public method, asserting params validation).

**Files:**
- Modify: `tests/test_client.py`

- [ ] **Step 1: Identify the duplicate success-path tests**

Run: `grep -n "test_get_.*_success\|async def test_get_scores\|async def test_get_responsiveness\|async def test_get_web\|async def test_get_speed\|async def test_get_wifi" tests/test_client.py`
Expected: a list of test method names — one per public client method. Note their line numbers.

- [ ] **Step 2: Add the parametrized replacement**

Append to `tests/test_client.py` (placement at end is fine; it's a new class):

```python
class TestPublicMethodsParametrized:
    """One test per dataset family, driven by DATASETS, replacing the per-method
    success-path tests for get_scores_1m / get_responsiveness / get_web_responsiveness
    / get_speed_results / get_wifi_link."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "family,method_name,sample_fixture,record_class",
        [
            ("scores", "get_scores_1m", "sample_scores_data", "ScoreRecord"),
            ("responsiveness", "get_responsiveness", "sample_responsiveness_data", "ResponsivenessRecord"),
            ("web_responsiveness", "get_web_responsiveness", "sample_web_responsiveness_data", "WebResponsivenessRecord"),
            ("speed_results", "get_speed_results", "sample_speed_data", "SpeedRecord"),
            ("wifi_link", "get_wifi_link", "sample_wifi_link_data", "WifiLinkRecord"),
        ],
    )
    async def test_public_method_returns_record_list(
        self, family, method_name, sample_fixture, record_class, request, mock_httpx_response
    ):
        from orbnet import models as models_module
        from orbnet.datasets import DATASETS

        sample_data = request.getfixturevalue(sample_fixture)
        record_cls = getattr(models_module, record_class)
        mock_httpx_response.json.return_value = sample_data

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_httpx_response

            client = OrbAPIClient(host="192.168.1.100")
            result = await getattr(client, method_name)()

            assert all(isinstance(r, record_cls) for r in result)
            assert len(result) == len(sample_data)

            url = mock_client.get.call_args[0][0]
            assert DATASETS[family].wire_name(DATASETS[family].default_granularity) in url
```

- [ ] **Step 3: Delete the superseded `test_get_<dataset>_success`-style tests**

Identify the duplicates from Step 1 and delete them. They typically look like:

```python
@pytest.mark.asyncio
async def test_get_scores_1m_success(self, sample_scores_data, mock_httpx_response):
    mock_httpx_response.json.return_value = sample_scores_data
    with patch("httpx.AsyncClient") as mock_client_class:
        ...
        result = await client.get_scores_1m()
        assert all(isinstance(r, ScoreRecord) for r in result)
        ...
```

Keep any tests that exercise other behavior (e.g. `test_get_responsiveness_with_granularity` exercises the granularity arg specifically — keep those). Only delete the bare success-path tests now subsumed by the parametrized version.

- [ ] **Step 4: Run full test suite**

Run: `uv run pytest tests/ -q`
Expected: roughly equivalent test count (5 deleted, 5 new parametrized cases) but all pass.

- [ ] **Step 5: Run with verbose to confirm parametrization**

Run: `uv run pytest tests/test_client.py::TestPublicMethodsParametrized -v`
Expected: 5 parametrized cases all PASS.

- [ ] **Step 6: Commit**

Pause and surface this proposed commit message; wait for approval.

```bash
git add tests/test_client.py
git commit -m "test(client): parametrize per-dataset success tests over DATASETS

Per-method success-path tests collapse to one parametrized test driven by
the registry. Adding a new dataset is one DATASETS entry plus one fixture —
no new test method required."
```

---

## Task 12: Update `mcp_server.py` docstring example, run lints, finalize

**Files:**
- Modify: `src/orbnet/mcp_server.py` (the `get_all_datasets` MCP tool docstring example, around line 552-559)

- [ ] **Step 1: Read the current docstring example**

Run: `grep -n "isinstance.*dict" src/orbnet/mcp_server.py`
Expected: a line reference inside `get_all_datasets`'s docstring showing the old `isinstance(data, dict) and 'error' in data` pattern.

- [ ] **Step 2: Update the Python-consumer example**

Locate the existing example block in `get_all_datasets`'s MCP-tool docstring. Replace the dict-shape example with:

```python
            For Python consumers, branch with is_ok() / .error:

            >>> from orbnet.models import is_ok, unwrap
            >>> result = await get_all_datasets()
            >>> for field_name in ("scores_1m", "responsiveness_1s", "speed_results"):
            ...     value = getattr(result, field_name)
            ...     if is_ok(value):
            ...         print(f"{field_name}: {len(value)} records")
            ...     else:
            ...         print(f"{field_name} failed: {value.error}")

            For LLM/JSON consumers, the wire format is unchanged — successful
            datasets serialize to a list, failed datasets to {"error": "..."}.
```

(Remove the older `isinstance(data, dict) and 'error' in data` example.)

- [ ] **Step 3: Run lint and format checks**

Run: `uv run --with ruff ruff check src/ tests/`
Expected: no errors. (If errors: fix them.)

Run: `uv run --with ruff ruff format --check src/ tests/`
Expected: no diffs. (If diffs reported: run `uv run --with ruff ruff format src/ tests/` and re-check.)

- [ ] **Step 4: Verify acceptance criteria from the spec**

Run each:

```bash
git grep -n "isinstance.*dict.*error" src/ tests/
```
Expected: no output (the bare-dict-error pattern is gone).

```bash
git grep -n "\[ScoreRecord\|\[ResponsivenessRecord\|\[WebResponsivenessRecord\|\[SpeedRecord\|\[WifiLinkRecord" src/orbnet/client.py
```
Expected: no output (record-class instantiation lives only in `_fetch`).

```bash
git grep -n '"error":' src/orbnet/
```
Expected: shows only the `ErrorPayload` class definition in `models.py` (no remaining dict literals in `client.py`).

- [ ] **Step 5: Run full test suite one final time**

Run: `uv run pytest tests/ -q`
Expected: all tests pass.

- [ ] **Step 6: Commit**

Pause and surface this proposed commit message; wait for approval.

```bash
git add src/orbnet/mcp_server.py
git commit -m "docs(mcp): update get_all_datasets docstring for typed error branch

Show is_ok/.error pattern for Python consumers; clarify that the JSON
wire format for LLM consumers is unchanged."
```

- [ ] **Step 7: Open PR**

Run: `git push -u origin dataset-registry-and-result`

Then create the PR (pause first to confirm with the user; PR creation is user-visible action):

```bash
gh pr create --title "Dataset registry + ErrorPayload result type" --body "$(cat <<'EOF'
## Summary
- New `src/orbnet/datasets.py` is the single source of truth for dataset metadata; `client.py`'s three parallel listings (six methods, `poll_dataset` dict, `get_all_datasets` task dict) now derive from it.
- `AllDatasetsResponse` Python error branch is a typed `ErrorPayload` instead of a bare dict; JSON wire format unchanged.
- All six public client methods, MCP tool surface, `poll_dataset` accepted inputs, and callback contracts are preserved.

## Test plan
- [ ] `uv run pytest tests/ -q` passes
- [ ] `uv run --with ruff ruff check src/ tests/` clean
- [ ] `uv run --with ruff ruff format --check src/ tests/` clean
- [ ] Manual sanity: `git grep "isinstance.*dict.*error" src/ tests/` returns nothing

See `docs/superpowers/specs/2026-05-02-dataset-registry-and-result-design.md` for design rationale.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## Acceptance criteria (from the spec)

- [ ] `uv run pytest tests/ -q` passes.
- [ ] Adding a hypothetical new dataset is one `DATASETS` entry + corresponding public shim + `AllDatasetsResponse` field; no `poll_dataset` or `get_all_datasets` edit required.
- [ ] No `[ScoreRecord(**` / `[ResponsivenessRecord(**` etc. patterns remain in `src/orbnet/client.py` outside `_fetch`.
- [ ] No `isinstance.*dict.*error` patterns remain in `src/orbnet` or `tests/`.
- [ ] `git grep '"error":' src/orbnet/` shows only the `ErrorPayload` definition.
