import asyncio
import uuid
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
    """Client for interacting with Orb.net Local Data API"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 7080,
        caller_id: Optional[str] = None,
        client_id: Optional[str] = None,
        timeout: float = 30.0,
        use_https: bool = False,
    ):
        """
        Initialize the Orb API client.

        Args:
            host: Hostname or IP address of the Orb sensor (default: "localhost")
            port: Port number for the Orb API (default: 7080)
            caller_id: Unique ID for this caller to track polling state.
                      If None, generates a random UUID. Use the same caller_id
                      across requests to only receive new records.
            client_id: Optional identifier for the HTTP client itself (sent as
                      User-Agent). Useful for identifying different applications
                      or services. If None, uses a default identifier.
            timeout: Request timeout in seconds
            use_https: If True, use HTTPS instead of HTTP (default: False)
        """
        self.config = OrbClientConfig(
            host=host,
            port=port,
            caller_id=caller_id or str(uuid.uuid4()),
            client_id=client_id or "orbnet", # TODO add version
            timeout=timeout,
            use_https=use_https,
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
    def use_https(self) -> bool:
        """Get the configured HTTPS setting"""
        return self.config.use_https

    @property
    def base_url(self) -> str:
        """Construct the base URL from host and port"""
        scheme = "https" if self.config.use_https else "http"
        return f"{scheme}://{self.config.host}:{self.config.port}"

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
        """
        request = DatasetRequestParams(format=format, caller_id=caller_id, **params)
        return await self._get_dataset(
            "speed_results", request.format, request.caller_id, **params
        )

