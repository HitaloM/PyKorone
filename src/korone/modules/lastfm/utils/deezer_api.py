# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from typing import Any

import httpx

from .types import DeezerData


class DeezerError(Exception):
    pass


class DeezerClient:
    __slots__ = ("base_url",)

    def __init__(self):
        self.base_url = "https://api.deezer.com/"

    async def _request(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(http2=True, timeout=20) as client:
                response = await client.get(f"{self.base_url}{endpoint}", params=params)
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException as timeout_error:
            msg = "API request timed out"
            raise DeezerError(msg) from timeout_error
        except httpx.RequestError as request_error:
            msg = "API request failed due to network issues"
            raise DeezerError(msg) from request_error
        except httpx.HTTPError as http_error:
            msg = "API request failed"
            raise DeezerError(msg) from http_error

    async def get_artist(self, artist_name: str) -> DeezerData:
        response_data = await self._request("search/artist", {"q": artist_name, "limit": 1})

        if not response_data["data"]:
            msg = "No artist found."
            raise DeezerError(msg)

        artist_info = response_data["data"][0]
        if artist_info.get("type") != "artist":
            msg = "No artist found."
            raise DeezerError(msg)

        if not artist_info.get("picture"):
            msg = "No image found for the artist."
            raise DeezerError(msg)

        try:
            return DeezerData.model_validate(artist_info)
        except KeyError as e:
            msg = f"Missing key in response data: {e}"
            raise DeezerError(msg) from e
