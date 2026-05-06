"""Dataset-fetch transport seam.

`OrbAPIClient` does not speak HTTP directly; it composes a `DatasetTransport`
that takes a wire-name and query params and returns the parsed JSON list.
Production code uses `HttpxDatasetTransport`; tests use a fake.

The seam exists so test code never has to mock `httpx.AsyncClient` to
exercise client behavior. Two adapters (httpx + fake) make the seam real.
"""

from typing import Any, Protocol

import httpx


class DatasetTransport(Protocol):
    """Port for fetching raw dataset records by wire name."""

    async def fetch_dataset(
        self, wire_name: str, params: dict[str, Any]
    ) -> list[dict[str, Any]]: ...


class HttpxDatasetTransport:
    """Production adapter: GET against the Orb Local Data API.

    Per-call lifecycle: opens a fresh `httpx.AsyncClient` for each fetch and
    closes it via `async with`. No long-lived client; no `aclose()` to manage.
    """

    def __init__(
        self,
        host: str,
        port: int,
        client_id: str,
        timeout: float,
    ):
        self._host = host
        self._port = port
        self._client_id = client_id
        self._timeout = timeout

    async def fetch_dataset(
        self, wire_name: str, params: dict[str, Any]
    ) -> list[dict[str, Any]]:
        endpoint = f"http://{self._host}:{self._port}/api/v2/datasets/{wire_name}.json"
        headers = {"Accept": "application/json", "User-Agent": self._client_id}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(endpoint, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
