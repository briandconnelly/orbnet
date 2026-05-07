"""
Tests for OrbAPIClient in orbnet.client.
"""

import asyncio
from unittest.mock import MagicMock

import httpx
import pytest

from orbnet.client import OrbAPIClient
from orbnet.models import (
    AllDatasetsResponse,
    ResponsivenessRecord,
    ScoreRecord,
    SpeedRecord,
    WebResponsivenessRecord,
    WifiLinkRecord,
)


class TestOrbAPIClient:
    """Test OrbAPIClient class."""

    def test_init_default_values(self):
        """Test client initialization with default values."""
        client = OrbAPIClient(host="192.168.1.100")
        assert client.host == "192.168.1.100"
        assert client.port == 7080
        assert client.caller_id is not None  # Should generate UUID
        assert client.client_id.startswith("orbnet/")
        assert client.timeout == 30.0

    def test_init_custom_values(self):
        """Test client initialization with custom values."""
        client = OrbAPIClient(
            host="192.168.1.100",
            port=8080,
            caller_id="test-caller",
            client_id="test-client",
            timeout=60.0,
        )
        assert client.host == "192.168.1.100"
        assert client.port == 8080
        assert client.caller_id == "test-caller"
        assert client.client_id == "test-client"
        assert client.timeout == 60.0

    def test_base_url_property(self):
        """Test base_url property construction."""
        client = OrbAPIClient(host="example.com", port=9000)
        assert client.base_url == "http://example.com:9000"

    @pytest.mark.asyncio
    async def test_get_responsiveness_1m(
        self, sample_responsiveness_data, fake_transport
    ):
        """Test get_responsiveness method with 1m granularity returns
        ResponsivenessRecord objects."""
        fake_transport.responses["responsiveness_1m"] = sample_responsiveness_data

        client = OrbAPIClient(host="192.168.1.100", transport=fake_transport)
        result = await client.get_responsiveness(granularity="1m")

        # Check result is a list of ResponsivenessRecord objects
        assert isinstance(result, list)
        assert len(result) == len(sample_responsiveness_data)
        assert all(isinstance(r, ResponsivenessRecord) for r in result)

        # Check data integrity
        assert result[0].orb_id == sample_responsiveness_data[0]["orb_id"]
        assert result[0].lag_avg_us == sample_responsiveness_data[0]["lag_avg_us"]
        assert (
            result[0].packet_loss_pct
            == sample_responsiveness_data[0]["packet_loss_pct"]
        )

        assert fake_transport.calls[-1][0] == "responsiveness_1m"

    @pytest.mark.asyncio
    async def test_get_responsiveness_1s(
        self, sample_responsiveness_data, fake_transport
    ):
        """Test get_responsiveness method with 1s granularity."""
        fake_transport.responses["responsiveness_1s"] = sample_responsiveness_data

        client = OrbAPIClient(host="192.168.1.100", transport=fake_transport)
        result = await client.get_responsiveness(granularity="1s")

        assert isinstance(result, list)
        assert all(isinstance(r, ResponsivenessRecord) for r in result)
        assert fake_transport.calls[-1][0] == "responsiveness_1s"

    @pytest.mark.asyncio
    async def test_get_responsiveness_15s(
        self, sample_responsiveness_data, fake_transport
    ):
        """Test get_responsiveness method with 15s granularity."""
        fake_transport.responses["responsiveness_15s"] = sample_responsiveness_data

        client = OrbAPIClient(host="192.168.1.100", transport=fake_transport)
        result = await client.get_responsiveness(granularity="15s")

        assert isinstance(result, list)
        assert all(isinstance(r, ResponsivenessRecord) for r in result)
        assert fake_transport.calls[-1][0] == "responsiveness_15s"

    @pytest.mark.asyncio
    async def test_get_wifi_link_1m(self, sample_wifi_link_data, fake_transport):
        """Test get_wifi_link with 1m granularity returns WifiLinkRecord objects."""
        fake_transport.responses["wifi_link_1m"] = sample_wifi_link_data

        client = OrbAPIClient(host="192.168.1.100", transport=fake_transport)
        result = await client.get_wifi_link(granularity="1m")

        assert isinstance(result, list)
        assert len(result) == len(sample_wifi_link_data)
        assert all(isinstance(r, WifiLinkRecord) for r in result)

        assert result[0].orb_id == sample_wifi_link_data[0]["orb_id"]
        assert result[0].rssi_avg == sample_wifi_link_data[0]["rssi_avg"]
        assert result[0].channel_band == sample_wifi_link_data[0]["channel_band"]

        assert fake_transport.calls[-1][0] == "wifi_link_1m"

    @pytest.mark.asyncio
    async def test_get_wifi_link_1s(self, sample_wifi_link_data, fake_transport):
        """Test get_wifi_link method with 1s granularity."""
        fake_transport.responses["wifi_link_1s"] = sample_wifi_link_data

        client = OrbAPIClient(host="192.168.1.100", transport=fake_transport)
        result = await client.get_wifi_link(granularity="1s")

        assert isinstance(result, list)
        assert all(isinstance(r, WifiLinkRecord) for r in result)
        assert fake_transport.calls[-1][0] == "wifi_link_1s"

    @pytest.mark.asyncio
    async def test_get_wifi_link_15s(self, sample_wifi_link_data, fake_transport):
        """Test get_wifi_link method with 15s granularity."""
        fake_transport.responses["wifi_link_15s"] = sample_wifi_link_data

        client = OrbAPIClient(host="192.168.1.100", transport=fake_transport)
        result = await client.get_wifi_link(granularity="15s")

        assert isinstance(result, list)
        assert all(isinstance(r, WifiLinkRecord) for r in result)
        assert fake_transport.calls[-1][0] == "wifi_link_15s"

    @pytest.mark.asyncio
    async def test_get_all_datasets_basic(
        self,
        sample_scores_data,
        sample_responsiveness_data,
        sample_web_responsiveness_data,
        sample_speed_data,
        sample_wifi_link_data,
        fake_transport,
    ):
        """Test get_all_datasets method returns AllDatasetsResponse."""
        responses = {
            "scores_1m": sample_scores_data,
            "responsiveness_1m": sample_responsiveness_data,
            "web_responsiveness_results": sample_web_responsiveness_data,
            "speed_results": sample_speed_data,
            "wifi_link_1m": sample_wifi_link_data,
        }

        client = OrbAPIClient(host="192.168.1.100", transport=fake_transport)
        fake_transport.responses.update(responses)
        result = await client.get_all_datasets()

        # Check result is AllDatasetsResponse
        assert isinstance(result, AllDatasetsResponse)

        # Check all required datasets are present
        assert isinstance(result.scores_1m, list)
        assert isinstance(result.responsiveness_1m, list)
        assert isinstance(result.web_responsiveness, list)
        assert isinstance(result.speed_results, list)
        assert isinstance(result.wifi_link_1m, list)

        # Check data types
        assert all(isinstance(r, ScoreRecord) for r in result.scores_1m)
        assert all(
            isinstance(r, ResponsivenessRecord) for r in result.responsiveness_1m
        )
        assert all(
            isinstance(r, WebResponsivenessRecord) for r in result.web_responsiveness
        )
        assert all(isinstance(r, SpeedRecord) for r in result.speed_results)
        assert all(isinstance(r, WifiLinkRecord) for r in result.wifi_link_1m)

    @pytest.mark.asyncio
    async def test_get_all_datasets_with_all_wifi_link(
        self,
        sample_scores_data,
        sample_responsiveness_data,
        sample_web_responsiveness_data,
        sample_speed_data,
        sample_wifi_link_data,
        fake_transport,
    ):
        """Test get_all_datasets method with all Wi-Fi Link granularities."""
        responses = {
            "scores_1m": sample_scores_data,
            "responsiveness_1m": sample_responsiveness_data,
            "web_responsiveness_results": sample_web_responsiveness_data,
            "speed_results": sample_speed_data,
            "wifi_link_1m": sample_wifi_link_data,
            "wifi_link_15s": sample_wifi_link_data,
            "wifi_link_1s": sample_wifi_link_data,
        }

        client = OrbAPIClient(host="192.168.1.100", transport=fake_transport)
        fake_transport.responses.update(responses)
        result = await client.get_all_datasets(include_all_wifi_link=True)

        assert isinstance(result, AllDatasetsResponse)
        assert isinstance(result.wifi_link_1m, list)
        assert isinstance(result.wifi_link_15s, list)
        assert isinstance(result.wifi_link_1s, list)
        assert all(isinstance(r, WifiLinkRecord) for r in result.wifi_link_1m)

    @pytest.mark.asyncio
    async def test_get_all_datasets_with_all_responsiveness(
        self,
        sample_scores_data,
        sample_responsiveness_data,
        sample_web_responsiveness_data,
        sample_speed_data,
        sample_wifi_link_data,
        fake_transport,
    ):
        """Test get_all_datasets method with all responsiveness granularities."""
        responses = {
            "scores_1m": sample_scores_data,
            "responsiveness_1m": sample_responsiveness_data,
            "responsiveness_15s": sample_responsiveness_data,
            "responsiveness_1s": sample_responsiveness_data,
            "web_responsiveness_results": sample_web_responsiveness_data,
            "speed_results": sample_speed_data,
            "wifi_link_1m": sample_wifi_link_data,
        }

        client = OrbAPIClient(host="192.168.1.100", transport=fake_transport)
        fake_transport.responses.update(responses)
        result = await client.get_all_datasets(include_all_responsiveness=True)

        assert isinstance(result, AllDatasetsResponse)
        assert isinstance(result.scores_1m, list)
        assert isinstance(result.responsiveness_1m, list)
        assert isinstance(result.responsiveness_15s, list)
        assert isinstance(result.responsiveness_1s, list)
        assert isinstance(result.web_responsiveness, list)
        assert isinstance(result.speed_results, list)

    @pytest.mark.asyncio
    async def test_get_all_datasets_with_error(
        self,
        sample_scores_data,
        sample_web_responsiveness_data,
        sample_speed_data,
        sample_wifi_link_data,
        fake_transport,
    ):
        """Test get_all_datasets method with one dataset failing."""
        from orbnet.models import ErrorPayload

        responses = {
            "scores_1m": sample_scores_data,
            "web_responsiveness_results": sample_web_responsiveness_data,
            "speed_results": sample_speed_data,
            "wifi_link_1m": sample_wifi_link_data,
        }

        client = OrbAPIClient(host="192.168.1.100", transport=fake_transport)
        fake_transport.responses.update(responses)
        fake_transport.responses["responsiveness_1m"] = Exception("Connection error")
        result = await client.get_all_datasets()

        assert isinstance(result, AllDatasetsResponse)
        assert isinstance(result.scores_1m, list)
        assert isinstance(result.responsiveness_1m, ErrorPayload)
        assert result.responsiveness_1m.error == "Connection error"
        assert isinstance(result.web_responsiveness, list)
        assert isinstance(result.speed_results, list)

    @pytest.mark.asyncio
    async def test_poll_dataset_success(self, sample_scores_data, fake_transport):
        """Test poll_dataset method with successful polling returns Pydantic objects."""
        fake_transport.responses["scores_1m"] = sample_scores_data

        client = OrbAPIClient(host="192.168.1.100", transport=fake_transport)

        # Test with max_iterations=2
        results = []
        async for records in client.poll_dataset(
            "scores_1m", interval=0.01, max_iterations=2
        ):
            results.append(records)

        assert len(results) == 2
        # Check all results are lists of ScoreRecord objects
        assert all(isinstance(r, list) for r in results)
        assert all(isinstance(rec, ScoreRecord) for r in results for rec in r)

    @pytest.mark.asyncio
    async def test_poll_dataset_with_callback(self, sample_scores_data, fake_transport):
        """Test poll_dataset method with callback function."""
        fake_transport.responses["scores_1m"] = sample_scores_data
        callback_calls = []

        def test_callback(dataset_name, records):
            callback_calls.append((dataset_name, records))

        client = OrbAPIClient(host="192.168.1.100", transport=fake_transport)

        # Test with max_iterations=1
        results = []
        async for records in client.poll_dataset(
            "scores_1m", interval=0.01, max_iterations=1, callback=test_callback
        ):
            results.append(records)

        assert len(results) == 1
        assert len(callback_calls) == 1
        assert callback_calls[0][0] == "scores_1m"
        # Check callback received Pydantic objects
        assert all(isinstance(r, ScoreRecord) for r in callback_calls[0][1])

    @pytest.mark.asyncio
    async def test_poll_dataset_with_async_callback(
        self, sample_scores_data, fake_transport
    ):
        """Test poll_dataset method with async callback function."""
        fake_transport.responses["scores_1m"] = sample_scores_data
        callback_calls = []

        async def test_async_callback(dataset_name, records):
            callback_calls.append((dataset_name, records))

        client = OrbAPIClient(host="192.168.1.100", transport=fake_transport)

        # Test with max_iterations=1
        results = []
        async for records in client.poll_dataset(
            "scores_1m",
            interval=0.01,
            max_iterations=1,
            callback=test_async_callback,
        ):
            results.append(records)

        assert len(results) == 1
        assert len(callback_calls) == 1
        assert callback_calls[0][0] == "scores_1m"
        # Check callback received Pydantic objects
        assert all(isinstance(r, ScoreRecord) for r in callback_calls[0][1])

    @pytest.mark.asyncio
    async def test_poll_dataset_awaits_partial_of_async_callback(
        self, sample_scores_data, fake_transport
    ):
        """`functools.partial(async_fn, ...)` returns a coroutine when called.
        The dispatch must await it regardless of how `partial` is classified
        by `asyncio.iscoroutinefunction` (which varies by Python version)."""
        import functools

        fake_transport.responses["scores_1m"] = sample_scores_data
        observed = []

        async def async_fn(prefix, dataset_name, records):
            observed.append((prefix, dataset_name, len(records)))

        partial_callback = functools.partial(async_fn, "tag")

        client = OrbAPIClient(host="192.168.1.100", transport=fake_transport)

        async for _ in client.poll_dataset(
            "scores_1m",
            interval=0.01,
            max_iterations=1,
            callback=partial_callback,
        ):
            pass

        assert observed == [("tag", "scores_1m", len(sample_scores_data))]

    @pytest.mark.asyncio
    async def test_poll_dataset_awaits_sync_callable_returning_coroutine(
        self, sample_scores_data, fake_transport
    ):
        """A sync function that builds and returns a coroutine should also
        have that coroutine awaited (covers async-lambda-like patterns)."""
        fake_transport.responses["scores_1m"] = sample_scores_data
        observed = []

        async def _record(dataset_name, records):
            observed.append((dataset_name, len(records)))

        def sync_returning_coro(dataset_name, records):
            return _record(dataset_name, records)

        # Sanity check: this is the shape that asyncio.iscoroutinefunction
        # cannot detect — without inspect.isawaitable on the *result*, the
        # returned coroutine would be silently dropped.
        assert not asyncio.iscoroutinefunction(sync_returning_coro)

        client = OrbAPIClient(host="192.168.1.100", transport=fake_transport)

        async for _ in client.poll_dataset(
            "scores_1m",
            interval=0.01,
            max_iterations=1,
            callback=sync_returning_coro,
        ):
            pass

        assert observed == [("scores_1m", len(sample_scores_data))]

    @pytest.mark.asyncio
    async def test_poll_dataset_with_error(self, fake_transport, caplog):
        """Test poll_dataset method with HTTP error."""
        import logging

        fake_transport.responses["scores_1m"] = httpx.HTTPStatusError(
            "500 Internal Server Error",
            request=MagicMock(),
            response=MagicMock(),
        )

        client = OrbAPIClient(host="192.168.1.100", transport=fake_transport)

        # Test with max_iterations=1 - should handle error gracefully
        results = []
        with caplog.at_level(logging.WARNING, logger="orbnet.client"):
            async for records in client.poll_dataset(
                "scores_1m", interval=0.01, max_iterations=1
            ):
                results.append(records)

        # When an error occurs, the generator doesn't yield anything
        # The error is logged but no results are yielded
        assert len(results) == 0
        assert len(caplog.records) == 1
        assert caplog.records[0].levelno == logging.WARNING
        assert "scores_1m" in caplog.records[0].message

    @pytest.mark.asyncio
    async def test_poll_dataset_invalid_dataset_name(self):
        """Test poll_dataset method with invalid dataset name."""
        client = OrbAPIClient(host="192.168.1.100")

        with pytest.raises(ValueError, match="Unknown dataset"):
            async for _ in client.poll_dataset(
                "invalid_dataset", interval=0.01, max_iterations=1
            ):
                pass

    @pytest.mark.asyncio
    async def test_poll_dataset_infinite(self, sample_scores_data, fake_transport):
        """Test poll_dataset method with infinite polling (max_iterations=None)."""
        fake_transport.responses["scores_1m"] = sample_scores_data

        client = OrbAPIClient(host="192.168.1.100", transport=fake_transport)

        # Test with max_iterations=None and short interval
        # We'll manually break after a few iterations
        results = []
        count = 0
        async for records in client.poll_dataset(
            "scores_1m", interval=0.01, max_iterations=None
        ):
            results.append(records)
            count += 1
            if count >= 3:  # Break after 3 iterations
                break

        assert len(results) == 3
        assert all(isinstance(r, list) for r in results)
        assert all(isinstance(rec, ScoreRecord) for r in results for rec in r)


class TestFetchHelper:
    """Direct tests for the private _fetch helper on OrbAPIClient."""

    @pytest.mark.asyncio
    async def test_fetch_passes_wire_name_and_maps_records(
        self, sample_scores_data, fake_transport
    ):
        from orbnet.datasets import DATASETS

        fake_transport.responses["scores_1m"] = sample_scores_data

        client = OrbAPIClient(host="192.168.1.100", transport=fake_transport)
        result = await client._fetch(DATASETS["scores"], "1m")

        assert fake_transport.calls[-1][0] == "scores_1m"
        assert all(isinstance(r, ScoreRecord) for r in result)
        assert len(result) == len(sample_scores_data)

    @pytest.mark.asyncio
    async def test_fetch_uses_default_granularity_when_omitted(
        self, sample_responsiveness_data, fake_transport
    ):
        from orbnet.datasets import DATASETS

        fake_transport.responses["responsiveness_1m"] = sample_responsiveness_data

        client = OrbAPIClient(host="192.168.1.100", transport=fake_transport)
        await client._fetch(DATASETS["responsiveness"])

        assert fake_transport.calls[-1][0] == "responsiveness_1m"

    @pytest.mark.asyncio
    async def test_fetch_honors_wire_name_override(
        self, sample_web_responsiveness_data, fake_transport
    ):
        from orbnet.datasets import DATASETS

        fake_transport.responses["web_responsiveness_results"] = (
            sample_web_responsiveness_data
        )

        client = OrbAPIClient(host="192.168.1.100", transport=fake_transport)
        await client._fetch(DATASETS["web_responsiveness"])

        assert fake_transport.calls[-1][0] == "web_responsiveness_results"

    @pytest.mark.asyncio
    async def test_fetch_threads_caller_id_override_into_params(
        self, sample_scores_data, fake_transport
    ):
        """`_fetch` must pass an explicit caller_id override into the
        transport's params dict as `id`. The deleted `_get_dataset`
        test covered this contract; this asserts it directly at the
        client→transport seam."""
        from orbnet.datasets import DATASETS

        fake_transport.responses["scores_1m"] = sample_scores_data

        client = OrbAPIClient(host="192.168.1.100", transport=fake_transport)
        await client._fetch(DATASETS["scores"], "1m", caller_id="override-123")

        params = fake_transport.calls[-1][1]
        assert params["id"] == "override-123"

    @pytest.mark.asyncio
    async def test_fetch_uses_default_caller_id_when_no_override(
        self, sample_scores_data, fake_transport
    ):
        """When no caller_id is passed, `_fetch` must thread the
        client's configured caller_id (set in __init__) into params."""
        from orbnet.datasets import DATASETS

        fake_transport.responses["scores_1m"] = sample_scores_data

        client = OrbAPIClient(
            host="192.168.1.100",
            caller_id="configured-default",
            transport=fake_transport,
        )
        await client._fetch(DATASETS["scores"], "1m")

        params = fake_transport.calls[-1][1]
        assert params["id"] == "configured-default"

    @pytest.mark.asyncio
    async def test_fetch_passes_extra_params_to_transport(
        self, sample_scores_data, fake_transport
    ):
        """`_fetch`'s `**params` must reach the transport's params dict
        alongside `id`. The deleted `_get_dataset_with_extra_params`
        test covered this; this asserts the same contract via the seam."""
        from orbnet.datasets import DATASETS

        fake_transport.responses["scores_1m"] = sample_scores_data

        client = OrbAPIClient(host="192.168.1.100", transport=fake_transport)
        await client._fetch(
            DATASETS["scores"],
            "1m",
            start_time=1700000000000,
            end_time=1700000060000,
        )

        params = fake_transport.calls[-1][1]
        assert params["start_time"] == 1700000000000
        assert params["end_time"] == 1700000060000
        # `id` is always populated alongside extra params.
        assert "id" in params


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
        fake_transport,
    ):
        # Map dataset wire-name -> raw response.
        responses = {
            # scores only has "1m" granularity — fallback to "1m" even
            # when caller asks for "1s".
            "scores_1m": sample_scores_data,
            "responsiveness_1s": sample_responsiveness_data,
            "web_responsiveness_results": sample_web_responsiveness_data,
            "speed_results": sample_speed_data,
            "wifi_link_1s": sample_wifi_link_data,
        }

        client = OrbAPIClient(host="192.168.1.100", transport=fake_transport)
        fake_transport.responses.update(responses)
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
        fake_transport,
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

        client = OrbAPIClient(host="192.168.1.100", transport=fake_transport)
        fake_transport.responses.update(responses)
        result = await client.get_all_datasets(include_all_responsiveness=True)

        assert isinstance(result.responsiveness_1s, list)
        assert isinstance(result.responsiveness_15s, list)
        assert isinstance(result.responsiveness_1m, list)
        assert result.wifi_link_15s is None
        assert result.wifi_link_1s is None

    @pytest.mark.asyncio
    async def test_invalid_default_granularity_raises(self):
        from pydantic import ValidationError

        client = OrbAPIClient(host="192.168.1.100")
        with pytest.raises(ValidationError):
            await client.get_all_datasets(default_granularity="bogus")  # type: ignore[arg-type]  # ty: ignore[invalid-argument-type]  # noqa: E501


class TestPollDatasetCallbackContract:
    """The user-supplied dataset_name string must reach callbacks unchanged.

    Today's callers expect 'web_responsiveness_results' (not 'web_responsiveness'
    or some other normalization) to flow through to their callback's first arg.
    """

    @pytest.mark.asyncio
    async def test_callback_receives_wire_alias_verbatim(
        self, sample_web_responsiveness_data, fake_transport
    ):
        fake_transport.responses["web_responsiveness_results"] = (
            sample_web_responsiveness_data
        )

        captured: list[str] = []

        def callback(dataset_name, records):
            captured.append(dataset_name)

        client = OrbAPIClient(host="192.168.1.100", transport=fake_transport)
        async for _ in client.poll_dataset(
            "web_responsiveness_results",
            interval=0.01,
            callback=callback,
            max_iterations=1,
        ):
            pass

        assert captured == ["web_responsiveness_results"]


class TestPublicMethodsParametrized:
    """One test per dataset family, driven by DATASETS, replacing the per-method
    success-path tests for get_scores_1m / get_responsiveness / get_web_responsiveness
    / get_speed_results / get_wifi_link."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "family,method_name,sample_fixture,record_class",
        [
            ("scores", "get_scores_1m", "sample_scores_data", "ScoreRecord"),
            (
                "responsiveness",
                "get_responsiveness",
                "sample_responsiveness_data",
                "ResponsivenessRecord",
            ),
            (
                "web_responsiveness",
                "get_web_responsiveness",
                "sample_web_responsiveness_data",
                "WebResponsivenessRecord",
            ),
            ("speed_results", "get_speed_results", "sample_speed_data", "SpeedRecord"),
            ("wifi_link", "get_wifi_link", "sample_wifi_link_data", "WifiLinkRecord"),
        ],
    )
    async def test_public_method_returns_record_list(
        self,
        family,
        method_name,
        sample_fixture,
        record_class,
        request,
        fake_transport,
    ):
        from orbnet import models as models_module
        from orbnet.datasets import DATASETS

        sample_data = request.getfixturevalue(sample_fixture)
        record_cls = getattr(models_module, record_class)
        ds = DATASETS[family]
        fake_transport.responses[ds.wire_name(ds.default_granularity)] = sample_data

        client = OrbAPIClient(host="192.168.1.100", transport=fake_transport)
        result = await getattr(client, method_name)()

        assert all(isinstance(r, record_cls) for r in result)
        assert len(result) == len(sample_data)
        assert fake_transport.calls[-1][0] == ds.wire_name(ds.default_granularity)


class TestExplicitOverrideSemantics:
    """__init__ uses `is None` checks, not falsy fallbacks, so explicit
    empty-string overrides are honored rather than silently replaced.

    The one exception is `host`, which has min_length=1 in OrbClientConfig
    — an empty hostname produces a structurally invalid base URL like
    `http://:7080`, so it's rejected at construction.
    """

    def test_empty_host_is_rejected(self):
        """host="" should raise ValidationError (would yield invalid URL)."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            OrbAPIClient(host="")

    def test_empty_caller_id_is_preserved(self):
        """caller_id="" should be passed through, not replaced with a UUID."""
        client = OrbAPIClient(host="192.168.1.100", caller_id="")
        assert client.caller_id == ""

    def test_empty_client_id_is_preserved(self):
        """client_id="" should be passed through, not replaced with the default."""
        client = OrbAPIClient(host="192.168.1.100", client_id="")
        assert client.client_id == ""

    def test_none_caller_id_generates_uuid(self):
        """caller_id=None still generates a fresh UUID per docstring contract."""
        client = OrbAPIClient(host="192.168.1.100", caller_id=None)
        assert client.caller_id is not None
        assert client.caller_id != ""

    def test_none_client_id_uses_default(self):
        """client_id=None still uses the default 'orbnet/<version>' string."""
        client = OrbAPIClient(host="192.168.1.100", client_id=None)
        assert client.client_id.startswith("orbnet/")


class TestPollDatasetPropagatesProgrammingErrors:
    """poll_dataset only swallows transport (httpx) errors. Programming errors
    such as pydantic validation failures and callback bugs must propagate so
    the caller can surface them, instead of polling forever silently."""

    @pytest.mark.asyncio
    async def test_validation_error_propagates(self, fake_transport):
        """A malformed API response should raise ValidationError, not be swallowed."""
        from pydantic import ValidationError

        # Return data missing required fields → pydantic ValidationError
        fake_transport.responses["scores_1m"] = [{"orb_id": "x"}]

        client = OrbAPIClient(host="192.168.1.100", transport=fake_transport)

        with pytest.raises(ValidationError):
            async for _ in client.poll_dataset(
                "scores_1m", interval=0.01, max_iterations=1
            ):
                pass

    @pytest.mark.asyncio
    async def test_callback_error_propagates(self, sample_scores_data, fake_transport):
        """A buggy callback should propagate, not be silenced."""
        fake_transport.responses["scores_1m"] = sample_scores_data

        def buggy_callback(dataset_name, records):
            raise RuntimeError("callback bug")

        client = OrbAPIClient(host="192.168.1.100", transport=fake_transport)

        with pytest.raises(RuntimeError, match="callback bug"):
            async for _ in client.poll_dataset(
                "scores_1m",
                interval=0.01,
                callback=buggy_callback,
                max_iterations=1,
            ):
                pass


class TestGranularityValidation:
    """Public client methods used to get granularity validation as a side-effect
    of constructing a Pydantic request object. After dropping that dead-weight
    construction, _fetch validates against spec.granularities so dynamic callers
    still get a clear, local ValueError instead of an opaque HTTP 404."""

    @pytest.mark.asyncio
    async def test_get_responsiveness_rejects_invalid_granularity(self):
        client = OrbAPIClient(host="192.168.1.100")
        with pytest.raises(ValueError, match="Invalid granularity"):
            await client.get_responsiveness(granularity="2m")  # type: ignore[arg-type]  # ty: ignore[invalid-argument-type]  # noqa: E501

    @pytest.mark.asyncio
    async def test_get_wifi_link_rejects_invalid_granularity(self):
        client = OrbAPIClient(host="192.168.1.100")
        with pytest.raises(ValueError, match="Invalid granularity"):
            await client.get_wifi_link(granularity="2m")  # type: ignore[arg-type]  # ty: ignore[invalid-argument-type]  # noqa: E501

    @pytest.mark.asyncio
    async def test_validation_error_lists_valid_granularities(self):
        """The error message should tell the caller what granularities are valid."""
        client = OrbAPIClient(host="192.168.1.100")
        with pytest.raises(ValueError, match="1s, 15s, 1m"):
            await client.get_responsiveness(granularity="bogus")  # type: ignore[arg-type]  # ty: ignore[invalid-argument-type]  # noqa: E501


class TestGetAllDatasetsErrorContext:
    """When a per-fetch task in get_all_datasets raises, the resulting
    ErrorPayload must include the structured code/repair from
    translate_exception, with `tool` and `granularity` populated from the
    plan loop."""

    async def test_partial_404_includes_repair_arguments(self, fake_transport):
        from orbnet.models import ErrorPayload

        request = httpx.Request(
            "GET", "http://h:7080/api/v2/datasets/responsiveness_1s.json"
        )
        response = httpx.Response(404, request=request)
        fake_transport.responses["responsiveness_1s"] = httpx.HTTPStatusError(
            "404",
            request=request,
            response=response,
        )
        # Other datasets succeed with empty lists.
        for wire_name in (
            "scores_1m",
            "responsiveness_15s",
            "responsiveness_1m",
            "web_responsiveness_results",
            "speed_results",
            "wifi_link_1m",
        ):
            fake_transport.responses[wire_name] = []

        client = OrbAPIClient(host="h", transport=fake_transport)
        result = await client.get_all_datasets(include_all_responsiveness=True)

        partial = result.responsiveness_1s
        assert isinstance(partial, ErrorPayload)
        assert partial.code == "granularity_unavailable"
        assert partial.repair is not None
        assert partial.repair.tool == "orb_get_responsiveness"
        assert partial.repair.arguments == {"granularity": "15s"}
