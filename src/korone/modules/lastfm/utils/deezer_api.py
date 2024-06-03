# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from dataclasses import dataclass

import httpx


class DeezerError(Exception):
    pass


@dataclass(slots=True, frozen=True)
class DeezerImage:
    url: str

    @classmethod
    def from_dict(cls, data: dict, size: str = "xl"):
        return cls(url=data.get(f"picture_{size}", data.get(f"cover_{size}", "")))


@dataclass(slots=True, frozen=True)
class DeezerArtist:
    id: int
    name: str
    image: DeezerImage

    @classmethod
    def from_dict(cls, data: dict):
        return cls(id=data["id"], name=data["name"], image=DeezerImage.from_dict(data))


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
            data = response.json().get("data", [])
            if not data:
                msg = "No data found"
                raise DeezerError(msg)
            return data[0]

    async def get_artist(self, artist_name: str) -> DeezerArtist:
        params = {
            "q": artist_name,
            "limit": 1,
        }
        data = await self._request("search/artist", params)
        if data["type"] == "artist":
            return DeezerArtist.from_dict(data)
        msg = "No artist found"
        raise DeezerError(msg)
