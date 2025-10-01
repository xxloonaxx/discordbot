"""HTTP helper utilities for reusable JSON requests."""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping

import httpx


__all__ = ["JsonHttpClient", "HTTPError"]

HTTPError = httpx.HTTPError


class JsonHttpClient:
    """Lightweight wrapper around :class:`httpx.AsyncClient` for JSON APIs."""

    def __init__(self, *, timeout: float = 10.0) -> None:
        self._client = httpx.AsyncClient(timeout=timeout, follow_redirects=True)

    async def get(self, url: str, *, params: Mapping[str, Any] | None = None) -> MutableMapping[str, Any]:
        """Return the JSON body from a GET request."""

        response = await self._client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, MutableMapping):
            raise TypeError("Expected the response to be a JSON object")
        return data

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""

        await self._client.aclose()

    async def __aenter__(self) -> "JsonHttpClient":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()
