"""Single source of truth for dataset metadata.

Each entry in DATASETS captures everything callers need to know about a
dataset family: which Pydantic record class its rows decode to, what
granularities it supports, and how its name is rendered on the wire and
in AllDatasetsResponse.
"""

from dataclasses import dataclass

from .models import (
    BaseRecord,
    Granularity,
    ResponsivenessRecord,
    ScoreRecord,
    SpeedRecord,
    WebResponsivenessRecord,
    WifiLinkRecord,
)


@dataclass(frozen=True)
class DatasetSpec:
    """Metadata describing one dataset family.

    Three name spaces are tracked:

    - `family`: the registry key. Public-method names follow `get_<family>`,
      with the historical exception of `get_scores_1m` (family `scores`).
    - `wire_name(granularity)`: the URL-path component used by the Orb API.
      Equals `family` for non-granular datasets, `f"{family}_{granularity}"`
      for granular ones, or `wire_name_override` when set.
    - `response_field(granularity)`: which `AllDatasetsResponse` slot this
      result populates. Equals `family` for non-granular datasets and
      `f"{family}_{granularity}"` for granular ones. Never inherits the
      wire-name override (e.g. `web_responsiveness` field,
      `web_responsiveness_results` wire).
    """

    family: str
    record_class: type[BaseRecord]
    granularities: tuple[Granularity, ...] = ()
    default_granularity: Granularity | None = None
    wire_name_override: str | None = None

    def wire_name(self, granularity: Granularity | None = None) -> str:
        if self.wire_name_override is not None:
            return self.wire_name_override
        if self.granularities:
            return f"{self.family}_{granularity or self.default_granularity}"
        return self.family

    def response_field(self, granularity: Granularity | None = None) -> str:
        if self.granularities:
            return f"{self.family}_{granularity or self.default_granularity}"
        return self.family


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


def _build_poll_aliases(
    datasets: dict[str, DatasetSpec],
) -> dict[str, tuple[DatasetSpec, Granularity | None]]:
    aliases: dict[str, tuple[DatasetSpec, Granularity | None]] = {}
    for spec in datasets.values():
        if spec.granularities:
            for g in spec.granularities:
                aliases[spec.wire_name(g)] = (spec, g)
        else:
            aliases[spec.wire_name()] = (spec, None)
    return aliases


POLL_ALIASES: dict[str, tuple[DatasetSpec, Granularity | None]] = _build_poll_aliases(
    DATASETS
)


def parse_poll_alias(name: str) -> tuple[DatasetSpec, Granularity | None]:
    """Resolve a wire-name string (as accepted by poll_dataset) to (spec, granularity).

    Raises ValueError with the list of valid options if `name` is unknown.
    """
    if name not in POLL_ALIASES:
        raise ValueError(
            f"Unknown dataset: {name}. Valid options: {', '.join(sorted(POLL_ALIASES))}"
        )
    return POLL_ALIASES[name]
