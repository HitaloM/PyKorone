# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import httpx

from korone.modules.lastfm.utils.types import DeezerArtist, DeezerImage


class DeezerError(Exception):
    pass


class DeezerClient:
    __slots__ = ("base_url",)

    def __init__(self):
        self.base_url = "https://api.deezer.com/"

    async def _request(self, endpoint: str, params: dict) -> dict:
        async with httpx.AsyncClient(http2=True, timeout=20) as client:
            response = await client.get(f"{self.base_url}{endpoint}", params=params)
            if response.status_code != 200:
                msg = f"Error fetching data from Deezer API: {response.status_code}"
                raise DeezerError(msg)
            if data := response.json().get("data", []):
                return data[0]
            msg = "No data found"
            raise DeezerError(msg)

    async def get_artist(self, artist_name: str) -> DeezerArtist:
        params = {
            "q": artist_name,
            "limit": 1,
        }
        data = await self._request("search/artist", params)
        if data["type"] == "artist":
            return DeezerArtist(
                id=data["id"],
                name=data["name"],
                image=DeezerImage(
                    url=data.get(
                        "picture_xl",
                        data.get("cover_xl", ""),
                    ),
                ),
            )
        msg = "No artist found"
        raise DeezerError(msg)
