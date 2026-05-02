"""Tests for orbnet.datasets — DatasetSpec, DATASETS registry, POLL_ALIASES."""

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


class TestDatasetsRegistry:
    """Verify the registry has exactly the five expected families."""

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
