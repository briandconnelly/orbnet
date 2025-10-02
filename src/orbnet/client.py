import asyncio
import uuid
from importlib.metadata import version as get_version
from typing import Any, Callable, Dict, List, Literal, Optional, Union

import httpx

from .models import (
    AllDatasetsRequestParams,
    DatasetRequestParams,
    OrbClientConfig,
    PollingConfig,
    ResponsivenessRequestParams,
)


class OrbAPIClient:
    """
    Client for interacting with Orb.net Local Data API.

    The OrbAPIClient provides a high-level interface to retrieve network quality
    datasets from Orb sensors. It supports polling for new data, multiple
    granularities, and both JSON and JSONL output formats.

    Examples:
        Basic usage:

        >>> client = OrbAPIClient(host="192.168.1.100")
        >>> scores = await client.get_scores_1m()
        >>> print(f"Received {len(scores)} score records")

        Custom configuration for production monitoring:

        >>> client = OrbAPIClient(
        ...     host="192.168.1.100",
        ...     port=7080,
        ...     caller_id="production-monitor",
        ...     client_id="MyApp/1.0.0",
        ...     timeout=60.0
        ... )
        >>> datasets = await client.get_all_datasets()

    """

    def __init__(
        self,
        host: str,
        port: int = 7080,
        caller_id: Optional[str] = None,
        client_id: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize the Orb API client.

        Args:
            host: Hostname or IP address of the Orb sensor
            port: Port number for the Orb API (default: 7080)
            caller_id: Unique ID for this caller to track polling state.
                      If None, generates a random UUID. Use the same caller_id
                      across requests to only receive new records.
            client_id: Optional identifier for the HTTP client itself (sent as
                      User-Agent). Useful for identifying different applications
                      or services. If None, uses a default identifier.
            timeout: Request timeout in seconds (default: 30.0)

        Examples:
            Connect to Orb sensor:

            >>> client = OrbAPIClient(host="192.168.1.100")

            Connect with persistent caller_id for stateful polling:

            >>> client = OrbAPIClient(
            ...     host="192.168.1.100",
            ...     caller_id="my-monitoring-service",
            ...     client_id="NetworkMonitor/2.1.0"
            ... )

            Connect with custom timeout for slow networks:

            >>> client = OrbAPIClient(
            ...     host="192.168.1.100",
            ...     timeout=120.0
            ... )
        """
        self.config = OrbClientConfig(
            host=host,
            port=port,
            caller_id=caller_id or str(uuid.uuid4()),
            client_id=client_id or f"orbnet/{get_version('orbnet')}",
            timeout=timeout,
        )

    @property
    def host(self) -> str:
        """Get the configured host"""
        return self.config.host

    @property
    def port(self) -> int:
        """Get the configured port"""
        return self.config.port

    @property
    def caller_id(self) -> str:
        """Get the configured caller_id"""
        return self.config.caller_id

    @property
    def client_id(self) -> str:
        """Get the configured client_id"""
        return self.config.client_id

    @property
    def timeout(self) -> float:
        """Get the configured timeout"""
        return self.config.timeout

    @property
    def base_url(self) -> str:
        """Construct the base URL from host and port"""
        return f"http://{self.config.host}:{self.config.port}"

    def _get_headers(self) -> Dict[str, str]:
        """Get common headers for API requests"""
        return {"Accept": "application/json", "User-Agent": self.config.client_id}

    async def _get_dataset(
        self,
        dataset_name: str,
        format: Literal["json", "jsonl"] = "json",
        caller_id: Optional[str] = None,
        **params,
    ) -> Union[List[Dict[str, Any]], str]:
        """
        Internal method to fetch a dataset from the Local Data API.

        Args:
            dataset_name: Name of the dataset (e.g., "responsiveness_1s")
            format: Response format - "json" for array or "jsonl" for NDJSON
            caller_id: Override the default caller_id for this request
            **params: Additional query parameters

        Returns:
            List of records (for json) or NDJSON string (for jsonl)
        """
        caller = caller_id or self.config.caller_id
        endpoint = f"{self.base_url}/api/v2/datasets/{dataset_name}.{format}"

        query_params = {"id": caller, **params}

        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.get(
                endpoint, headers=self._get_headers(), params=query_params
            )
            response.raise_for_status()

            if format == "json":
                return response.json()
            else:  # jsonl
                return response.text

    async def get_scores_1m(
        self,
        format: Literal["json", "jsonl"] = "json",
        caller_id: Optional[str] = None,
        **params,
    ) -> Union[List[Dict[str, Any]], str]:
        """
        Retrieve 1-minute granularity Scores dataset.

        The Scores Dataset focuses on Orb Score, its component scores
        (Responsiveness, Reliability, and Speed), and underlying measures.
        Minimum granularity is 1 minute.

        Args:
            format: Response format - "json" for array or "jsonl" for NDJSON
            caller_id: Override the default caller_id for this request
            **params: Additional query parameters

        Returns:
            List of records or NDJSON string, each containing:
            - identifiers: ScoreIdentifiers (orb_id, orb_name, device_name, etc.)
            - measures: ScoreMeasures (orb_score, responsiveness_score, etc.)
            - dimensions: NetworkDimensions (network_type, country_code, etc.)

        Examples:
            Get latest scores and display overall quality:

            >>> client = OrbAPIClient(host="192.168.1.100")
            >>> scores = await client.get_scores_1m()
            >>> if scores:
            ...     latest = scores[-1]
            ...     print(f"Orb Score: {latest['orb_score']}")
            ...     print(f"Responsiveness: {latest['responsiveness_score']}")
            ...     print(f"Reliability: {latest['reliability_score']}")
            ...     print(f"Speed: {latest['speed_score']}")

            Calculate average score over the returned period:

            >>> scores = await client.get_scores_1m()
            >>> avg_score = sum(s['orb_score'] for s in scores) / len(scores)
            >>> print(f"Average Orb Score: {avg_score:.1f}")

            Get scores in JSONL format for streaming processing:

            >>> scores_jsonl = await client.get_scores_1m(format="jsonl")
            >>> for line in scores_jsonl.strip().split('\\n'):
            ...     record = json.loads(line)
            ...     print(f"Score at {record['timestamp']}: {record['orb_score']}")

            Check network quality by ISP:

            >>> scores = await client.get_scores_1m()
            >>> isp_scores = {}
            >>> for record in scores:
            ...     isp = record['isp_name']
            ...     if isp not in isp_scores:
            ...         isp_scores[isp] = []
            ...     isp_scores[isp].append(record['orb_score'])
            >>> for isp, scores_list in isp_scores.items():
            ...     avg = sum(scores_list) / len(scores_list)
            ...     print(f"{isp}: {avg:.1f}")
        """
        request = DatasetRequestParams(format=format, caller_id=caller_id, **params)
        return await self._get_dataset(
            "scores_1m", request.format, request.caller_id, **params
        )

    async def get_responsiveness(
        self,
        granularity: Literal["1s", "15s", "1m"] = "1m",
        format: Literal["json", "jsonl"] = "json",
        caller_id: Optional[str] = None,
        **params,
    ) -> Union[List[Dict[str, Any]], str]:
        """
        Retrieve Responsiveness dataset.

        Includes all measures related to network responsiveness, including
        lag, latency, jitter, and packet loss. Available in 1s, 15s, and 1m buckets.

        Args:
            granularity: Time bucket size - "1s", "15s", or "1m"
            format: Response format - "json" for array or "jsonl" for NDJSON
            caller_id: Override the default caller_id for this request
            **params: Additional query parameters

        Returns:
            List of records or NDJSON string, each containing:
            - identifiers: orb_id, orb_name, device_name, orb_version, timestamp
            - measures: ResponsivenessMeasures (lag_avg_us, latency_avg_us, etc.)
            - dimensions: NetworkDimensions + network_name, pingers

        Examples:
            Get high-resolution 1-second responsiveness data:

            >>> client = OrbAPIClient(host="192.168.1.100")
            >>> data = await client.get_responsiveness(granularity="1s")
            >>> if data:
            ...     latest = data[-1]
            ...     print(f"Lag: {latest['lag_avg_us']} μs")
            ...     print(f"Latency: {latest['latency_avg_us']} μs")
            ...     print(f"Jitter: {latest['jitter_avg_us']} μs")
            ...     print(f"Packet Loss: {latest['packet_loss_pct']:.2f}%")

            Monitor for high latency:

            >>> data = await client.get_responsiveness(granularity="1s")
            >>> threshold = 50000  # 50ms in microseconds
            >>> high_latency = [r for r in data if r['latency_avg_us'] > threshold]
            >>> if high_latency:
            ...     print(f"Warning: {len(high_latency)} records with high latency")

            Compare router vs internet latency:

            >>> data = await client.get_responsiveness(granularity="15s")
            >>> for record in data[-5:]:
            ...     internet_lat = record['latency_avg_us']
            ...     router_lat = record['router_latency_avg_us']
            ...     print(f"Internet: {internet_lat}μs, Router: {router_lat}μs")

            Track packet loss trends:

            >>> data = await client.get_responsiveness(granularity="1m")
            >>> loss_rates = [r['packet_loss_pct'] for r in data]
            >>> avg_loss = sum(loss_rates) / len(loss_rates)
            >>> max_loss = max(loss_rates)
            >>> print(f"Avg packet loss: {avg_loss:.2f}%, Max: {max_loss:.2f}%")
        """
        request = ResponsivenessRequestParams(
            granularity=granularity, format=format, caller_id=caller_id, **params
        )
        dataset_name = f"responsiveness_{request.granularity}"
        return await self._get_dataset(
            dataset_name, request.format, request.caller_id, **params
        )

    async def get_web_responsiveness(
        self,
        format: Literal["json", "jsonl"] = "json",
        caller_id: Optional[str] = None,
        **params,
    ) -> Union[List[Dict[str, Any]], str]:
        """
        Retrieve Web Responsiveness dataset.

        Includes Orb's measures of web responsiveness: Time to First Byte (TTFB)
        for web page load, and DNS resolver response time. Measurements are
        conducted once per minute by default (raw results, not aggregates).

        Args:
            format: Response format - "json" for array or "jsonl" for NDJSON
            caller_id: Override the default caller_id for this request
            **params: Additional query parameters

        Returns:
            List of records or NDJSON string, each containing:
            - identifiers: orb_id, orb_name, device_name, orb_version, timestamp
            - measures: WebResponsivenessMeasures (ttfb_us, dns_us)
            - dimensions: NetworkDimensions + network_name, web_url

        Examples:
            Monitor web browsing experience:

            >>> client = OrbAPIClient(host="192.168.1.100")
            >>> data = await client.get_web_responsiveness()
            >>> if data:
            ...     latest = data[-1]
            ...     ttfb_ms = latest['ttfb_us'] / 1000
            ...     dns_ms = latest['dns_us'] / 1000
            ...     print(f"TTFB: {ttfb_ms:.1f}ms, DNS: {dns_ms:.1f}ms")

            Check for slow DNS resolution:

            >>> data = await client.get_web_responsiveness()
            >>> slow_dns = [r for r in data if r['dns_us'] > 100000]  # >100ms
            >>> if slow_dns:
            ...     print(f"Found {len(slow_dns)} records with slow DNS")

            Analyze web performance over time:

            >>> data = await client.get_web_responsiveness()
            >>> ttfb_values = [r['ttfb_us'] / 1000 for r in data]
            >>> avg_ttfb = sum(ttfb_values) / len(ttfb_values)
            >>> print(f"Average TTFB: {avg_ttfb:.1f}ms")

            Compare different websites being tested:

            >>> data = await client.get_web_responsiveness()
            >>> by_url = {}
            >>> for record in data:
            ...     url = record['web_url']
            ...     if url not in by_url:
            ...         by_url[url] = []
            ...     by_url[url].append(record['ttfb_us'] / 1000)
            >>> for url, ttfbs in by_url.items():
            ...     avg = sum(ttfbs) / len(ttfbs)
            ...     print(f"{url}: {avg:.1f}ms avg TTFB")
        """
        request = DatasetRequestParams(format=format, caller_id=caller_id, **params)
        return await self._get_dataset(
            "web_responsiveness_results", request.format, request.caller_id, **params
        )

    async def get_speed_results(
        self,
        format: Literal["json", "jsonl"] = "json",
        caller_id: Optional[str] = None,
        **params,
    ) -> Union[List[Dict[str, Any]], str]:
        """
        Retrieve Speed dataset.

        Includes the results of Orb's speed tests. Content speed measurements
        are conducted once per hour by default (raw results, not aggregates).

        Args:
            format: Response format - "json" for array or "jsonl" for NDJSON
            caller_id: Override the default caller_id for this request
            **params: Additional query parameters

        Returns:
            List of records or NDJSON string, each containing:
            - identifiers: orb_id, orb_name, device_name, orb_version, timestamp
            - measures: SpeedMeasures (download_kbps, upload_kbps)
            - dimensions: NetworkDimensions + network_name, speed_test_engine,
                 speed_test_server

        Examples:
            Get latest speed test results:

            >>> client = OrbAPIClient(host="192.168.1.100")
            >>> speeds = await client.get_speed_results()
            >>> if speeds:
            ...     latest = speeds[-1]
            ...     down_mbps = latest['download_kbps'] / 1000
            ...     up_mbps = latest['upload_kbps'] / 1000
            ...     print(f"Download: {down_mbps:.1f} Mbps")
            ...     print(f"Upload: {up_mbps:.1f} Mbps")

            Track speed trends over time:

            >>> speeds = await client.get_speed_results()
            >>> downloads = [s['download_kbps'] / 1000 for s in speeds]
            >>> avg_speed = sum(downloads) / len(downloads)
            >>> min_speed = min(downloads)
            >>> max_speed = max(downloads)
            >>> print(f"Download: Avg={avg_speed:.1f}, Min={min_speed:.1f}, Max={max_speed:.1f} Mbps") # noqa: E501

            Check if speeds meet SLA requirements:

            >>> speeds = await client.get_speed_results()
            >>> required_mbps = 100
            >>> below_sla = [s for s in speeds
            ...              if s['download_kbps'] / 1000 < required_mbps]
            >>> if below_sla:
            ...     print(f"Warning: {len(below_sla)} tests below {required_mbps} Mbps")

            Compare different speed test servers:

            >>> speeds = await client.get_speed_results()
            >>> by_server = {}
            >>> for record in speeds:
            ...     server = record['speed_test_server']
            ...     if server not in by_server:
            ...         by_server[server] = []
            ...     by_server[server].append(record['download_kbps'] / 1000)
            >>> for server, speeds_list in by_server.items():
            ...     avg = sum(speeds_list) / len(speeds_list)
            ...     print(f"{server}: {avg:.1f} Mbps avg")
        """
        request = DatasetRequestParams(format=format, caller_id=caller_id, **params)
        return await self._get_dataset(
            "speed_results", request.format, request.caller_id, **params
        )

    async def get_all_datasets(
        self,
        format: Literal["json", "jsonl"] = "json",
        caller_id: Optional[str] = None,
        include_all_responsiveness: bool = False,
    ) -> Dict[str, Union[List[Dict[str, Any]], str]]:
        """
        Retrieve all datasets concurrently.

        Args:
            format: Response format - "json" for array or "jsonl" for NDJSON
            caller_id: Override the default caller_id for this request
            include_all_responsiveness: If True, fetches all responsiveness
                                       granularities (1s, 15s, 1m). If False,
                                       only fetches 1m granularity.

        Returns:
            Dictionary with keys for each dataset type containing their data

        Examples:
            Fetch all datasets at once:

            >>> client = OrbAPIClient(host="192.168.1.100")
            >>> datasets = await client.get_all_datasets()
            >>> print(f"Scores: {len(datasets['scores_1m'])} records")
            >>> print(f"Responsiveness: {len(datasets['responsiveness_1m'])} records")
            >>> print(f"Web: {len(datasets['web_responsiveness'])} records")
            >>> print(f"Speed: {len(datasets['speed_results'])} records")

            Fetch with all responsiveness granularities:

            >>> datasets = await client.get_all_datasets(
            ...     include_all_responsiveness=True
            ... )
            >>> print(f"1s: {len(datasets['responsiveness_1s'])} records")
            >>> print(f"15s: {len(datasets['responsiveness_15s'])} records")
            >>> print(f"1m: {len(datasets['responsiveness_1m'])} records")

            Create a comprehensive network report:

            >>> datasets = await client.get_all_datasets()
            >>> scores = datasets['scores_1m']
            >>> speeds = datasets['speed_results']
            >>>
            >>> if scores and speeds:
            ...     avg_score = sum(s['orb_score'] for s in scores) / len(scores)
            ...     latest_speed = speeds[-1]['download_kbps'] / 1000
            ...     print(f"Network Health: {avg_score:.1f}/100")
            ...     print(f"Current Speed: {latest_speed:.1f} Mbps")

            Handle errors gracefully:

            >>> datasets = await client.get_all_datasets()
            >>> for name, data in datasets.items():
            ...     if isinstance(data, dict) and 'error' in data:
            ...         print(f"Failed to fetch {name}: {data['error']}")
            ...     else:
            ...         print(f"{name}: {len(data)} records")
        """
        request = AllDatasetsRequestParams(
            format=format,
            caller_id=caller_id,
            include_all_responsiveness=include_all_responsiveness,
        )

        tasks = {
            "scores_1m": self.get_scores_1m(request.format, request.caller_id),
            "responsiveness_1m": self.get_responsiveness(
                "1m", request.format, request.caller_id
            ),
            "web_responsiveness": self.get_web_responsiveness(
                request.format, request.caller_id
            ),
            "speed_results": self.get_speed_results(request.format, request.caller_id),
        }

        if request.include_all_responsiveness:
            tasks["responsiveness_15s"] = self.get_responsiveness(
                "15s", request.format, request.caller_id
            )
            tasks["responsiveness_1s"] = self.get_responsiveness(
                "1s", request.format, request.caller_id
            )

        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        return {
            key: result if not isinstance(result, Exception) else {"error": str(result)}
            for key, result in zip(tasks.keys(), results, strict=True)
        }

    async def poll_dataset(
        self,
        dataset_name: str,
        interval: float = 60.0,
        format: Literal["json", "jsonl"] = "json",
        callback: Optional[Callable] = None,
        max_iterations: Optional[int] = None,
    ):
        """
        Continuously poll a dataset at regular intervals.

        This method automatically tracks state using the client's caller_id,
        so each poll will only return new records since the last request.

        Args:
            dataset_name: Name of the dataset to poll (e.g., "responsiveness_1s")
            interval: Seconds to wait between polls
            format: Response format - "json" for array or "jsonl" for NDJSON
            callback: Optional function to call with each batch of new records.
                     Should accept (dataset_name, records) as arguments.
            max_iterations: Maximum number of polls (None for infinite)

        Yields:
            Each batch of new records

        Examples:
            Poll for new responsiveness data every 10 seconds:

            >>> client = OrbAPIClient(host="192.168.1.100")
            >>> async for records in client.poll_dataset(
            ...     dataset_name="responsiveness_1s",
            ...     interval=10.0,
            ...     max_iterations=6  # Poll for 1 minute
            ... ):
            ...     if records:
            ...         latest = records[-1]
            ...         print(f"Lag: {latest['lag_avg_us']} μs")

            Monitor scores with a callback function:

            >>> def alert_on_low_score(dataset_name, records):
            ...     for record in records:
            ...         if record['orb_score'] < 50:
            ...             print(f"ALERT: Low score {record['orb_score']}")
            >>>
            >>> async for _ in client.poll_dataset(
            ...     dataset_name="scores_1m",
            ...     interval=60.0,
            ...     callback=alert_on_low_score,
            ...     max_iterations=10
            ... ):
            ...     pass  # Callback handles processing

            Continuous monitoring (infinite loop):

            >>> async for records in client.poll_dataset(
            ...     dataset_name="speed_results",
            ...     interval=300.0  # Every 5 minutes
            ... ):
            ...     if records:
            ...         for record in records:
            ...             speed_mbps = record['download_kbps'] / 1000
            ...             print(f"Speed test: {speed_mbps:.1f} Mbps")

            Build a real-time dashboard:

            >>> dashboard_data = {"latency": [], "scores": []}
            >>>
            >>> async def update_dashboard(dataset_name, records):
            ...     if dataset_name == "responsiveness_1s":
            ...         for r in records:
            ...             dashboard_data["latency"].append(r['latency_avg_us'])
            ...     elif dataset_name == "scores_1m":
            ...         for r in records:
            ...             dashboard_data["scores"].append(r['orb_score'])
            >>>
            >>> # In practice, you'd run these concurrently
            >>> async for _ in client.poll_dataset(
            ...     "responsiveness_1s",
            ...     interval=10.0,
            ...     callback=update_dashboard,
            ...     max_iterations=3
            ... ):
            ...     pass

            Poll with async callback:

            >>> async def async_callback(dataset_name, records):
            ...     # Perform async operations like writing to database
            ...     await database.insert_many(records)
            >>>
            >>> async for _ in client.poll_dataset(
            ...     "scores_1m",
            ...     callback=async_callback,
            ...     max_iterations=5
            ... ):
            ...     pass
        """
        config = PollingConfig(
            dataset_name=dataset_name,
            interval=interval,
            format=format,
            callback=callback,
            max_iterations=max_iterations,
        )

        iteration = 0
        while config.max_iterations is None or iteration < config.max_iterations:
            try:
                records = await self._get_dataset(config.dataset_name, config.format)

                if config.callback and records:
                    await config.callback(
                        config.dataset_name, records
                    ) if asyncio.iscoroutinefunction(
                        config.callback
                    ) else config.callback(config.dataset_name, records)

                yield records

                await asyncio.sleep(config.interval)
                iteration += 1

            except Exception as e:
                print(f"Error polling {config.dataset_name}: {e}")
                await asyncio.sleep(config.interval)
                iteration += 1
