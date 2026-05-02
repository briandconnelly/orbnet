"""Tests for orbnet.datasets — DatasetSpec, DATASETS registry, POLL_ALIASES."""

from orbnet.datasets import DatasetSpec
from orbnet.models import (
    ResponsivenessRecord,
    SpeedRecord,
    WebResponsivenessRecord,
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
