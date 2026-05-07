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
        spec = DatasetSpec(
            family="speed_results",
            record_class=SpeedRecord,
            tool_name="orb_get_speed_results",
        )
        assert spec.wire_name() == "speed_results"

    def test_non_granular_response_field(self):
        spec = DatasetSpec(
            family="speed_results",
            record_class=SpeedRecord,
            tool_name="orb_get_speed_results",
        )
        assert spec.response_field() == "speed_results"

    def test_granular_wire_name_explicit_granularity(self):
        spec = DatasetSpec(
            family="responsiveness",
            record_class=ResponsivenessRecord,
            tool_name="orb_get_responsiveness",
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
            tool_name="orb_get_responsiveness",
            granularities=("1s", "15s", "1m"),
            default_granularity="1m",
        )
        assert spec.wire_name() == "responsiveness_1m"

    def test_granular_response_field(self):
        spec = DatasetSpec(
            family="responsiveness",
            record_class=ResponsivenessRecord,
            tool_name="orb_get_responsiveness",
            granularities=("1s", "15s", "1m"),
            default_granularity="1m",
        )
        assert spec.response_field("1s") == "responsiveness_1s"
        assert spec.response_field() == "responsiveness_1m"

    def test_wire_name_override(self):
        spec = DatasetSpec(
            family="web_responsiveness",
            record_class=WebResponsivenessRecord,
            tool_name="orb_get_web_responsiveness",
            wire_name_override="web_responsiveness_results",
        )
        assert spec.wire_name() == "web_responsiveness_results"

    def test_response_field_unaffected_by_wire_name_override(self):
        """Field name must NOT inherit the override; AllDatasetsResponse uses
        `web_responsiveness`, not `web_responsiveness_results`."""
        spec = DatasetSpec(
            family="web_responsiveness",
            record_class=WebResponsivenessRecord,
            tool_name="orb_get_web_responsiveness",
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


class TestDatasetSpecToolName:
    """Each registry entry exposes its public MCP tool name. Used by both
    the MCP layer (for registration) and OrbAPIClient.get_all_datasets
    (to thread tool name into ErrorContext for the partial-failure path)."""

    def test_scores_tool_name(self):
        from orbnet.datasets import DATASETS

        assert DATASETS["scores"].tool_name == "orb_get_scores"

    def test_responsiveness_tool_name(self):
        from orbnet.datasets import DATASETS

        assert DATASETS["responsiveness"].tool_name == "orb_get_responsiveness"

    def test_web_responsiveness_tool_name(self):
        from orbnet.datasets import DATASETS

        assert DATASETS["web_responsiveness"].tool_name == "orb_get_web_responsiveness"

    def test_speed_results_tool_name(self):
        from orbnet.datasets import DATASETS

        assert DATASETS["speed_results"].tool_name == "orb_get_speed_results"

    def test_wifi_link_tool_name(self):
        from orbnet.datasets import DATASETS

        assert DATASETS["wifi_link"].tool_name == "orb_get_wifi_link"


class TestDatasetSpecValidateGranularity:
    """spec.validate_granularity(g) raises ValueError for granularities not
    in spec.granularities. Used by OrbAPIClient._fetch."""

    def test_valid_granularity_returns_none(self):
        from orbnet.datasets import DATASETS

        # No exception, returns None implicitly.
        result = DATASETS["responsiveness"].validate_granularity("1s")
        assert result is None

    def test_invalid_granularity_raises_value_error(self):
        import pytest

        from orbnet.datasets import DATASETS

        with pytest.raises(ValueError, match="Invalid granularity"):
            DATASETS["responsiveness"].validate_granularity("2m")  # type: ignore[arg-type]  # ty: ignore[invalid-argument-type]  # noqa: E501

    def test_error_message_lists_valid_granularities(self):
        import pytest

        from orbnet.datasets import DATASETS

        with pytest.raises(ValueError, match="1s, 15s, 1m"):
            DATASETS["responsiveness"].validate_granularity("bogus")  # type: ignore[arg-type]  # ty: ignore[invalid-argument-type]  # noqa: E501

    def test_non_granular_dataset_accepts_none(self):
        from orbnet.datasets import DATASETS

        # speed_results has no granularities; validating None is a no-op.
        result = DATASETS["speed_results"].validate_granularity(None)
        assert result is None

    def test_non_granular_dataset_silently_accepts_anything(self):
        """When spec.granularities is empty, validation is a no-op even
        for arbitrary input. Matches today's _fetch behavior (the inline
        check skipped validation when spec.granularities was empty)."""
        from orbnet.datasets import DATASETS

        # No exception even though "1s" isn't meaningful for this dataset.
        DATASETS["speed_results"].validate_granularity("1s")
