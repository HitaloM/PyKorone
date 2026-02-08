from __future__ import annotations

from typing import Any

import aiohttp

from korone.logger import get_logger
from korone.utils.aiohttp_session import HTTPClient

from .types import DeezerData

logger = get_logger(__name__)


class DeezerError(Exception):
    def __init__(self, message: str, response: aiohttp.ClientResponse | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.response = response


class DeezerClient:
    __slots__ = ("base_url", "timeout")

    def __init__(self, timeout: int = 20) -> None:
        self.base_url = "https://api.deezer.com/"
        self.timeout = timeout

    async def _request(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        timeout = aiohttp.ClientTimeout(total=self.timeout)

        try:
            session = await HTTPClient.get_session()
            async with session.get(url, params=params, timeout=timeout) as response:
                response.raise_for_status()
                data = await response.json()

                if "error" in data:
                    msg = f"API error: {data['error'].get('message', 'Unknown error')}"
                    raise DeezerError(msg, response)

                return data

        except aiohttp.ClientResponseError as exc:
            msg = f"API request failed with status code {exc.status}"
            await logger.aexception("[Deezer] HTTP error %s: %s", exc.status, exc)
            raise DeezerError(msg) from exc
        except aiohttp.ClientError as exc:
            msg = "API request failed"
            await logger.aexception("[Deezer] Request failed: %s", exc)
            raise DeezerError(msg) from exc
        except ValueError as exc:
            msg = "Failed to parse API response"
            await logger.aexception("[Deezer] Parse error: %s", exc)
            raise DeezerError(msg) from exc

    async def get_artist(self, artist_name: str) -> DeezerData:
        response_data = await self._request("search/artist", {"q": artist_name, "limit": 1})

        if not response_data.get("data"):
            msg = f"No artist found for '{artist_name}'"
            raise DeezerError(msg)

        artist_info = response_data["data"][0]
        if artist_info.get("type") != "artist":
            msg = f"Search result for '{artist_name}' isn't an artist"
            raise DeezerError(msg)

        if not artist_info.get("picture"):
            msg = f"No image found for artist '{artist_name}'"
            raise DeezerError(msg)

        try:
            return DeezerData.model_validate(artist_info)
        except ValueError as exc:
            msg = f"Failed to parse artist data: {exc}"
            raise DeezerError(msg) from exc
