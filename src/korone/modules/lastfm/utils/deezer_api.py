# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from typing import Any

import httpx

from korone.utils.logging import get_logger

from .types import DeezerData

logger = get_logger(__name__)


class DeezerError(Exception):
    def __init__(self, message: str, response: httpx.Response | None = None):
        super().__init__(message)
        self.message = message
        self.response = response


class DeezerClient:
    __slots__ = ("base_url", "timeout")

    def __init__(self, timeout: int = 20):
        self.base_url = "https://api.deezer.com/"
        self.timeout = timeout

    async def _request(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}{endpoint}"

        try:
            async with httpx.AsyncClient(http2=True, timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()

                data = response.json()

                if "error" in data:
                    msg = f"API error: {data['error'].get('message', 'Unknown error')}"
                    raise DeezerError(msg, response)

                return data

        except httpx.TimeoutException as e:
            msg = "API request timed out"
            await logger.aexception("[Deezer] Timeout: %s", e)
            raise DeezerError(msg) from e

        except httpx.RequestError as e:
            msg = "API request failed"
            await logger.aexception("[Deezer] Request failed: %s", e)
            raise DeezerError(msg) from e

        except httpx.HTTPStatusError as e:
            msg = f"API request failed with status code {e.response.status_code}"
            await logger.aexception("[Deezer] HTTP error %s: %s", e.response.status_code, e)
            raise DeezerError(msg, e.response) from e

        except ValueError as e:
            msg = "Failed to parse API response"
            await logger.aexception("[Deezer] Parse error: %s", e)
            raise DeezerError(msg) from e

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
        except ValueError as e:
            msg = f"Failed to parse artist data: {e}"
            raise DeezerError(msg) from e
