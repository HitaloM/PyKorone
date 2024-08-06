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
            try:
                response = await client.get(f"{self.base_url}{endpoint}", params=params)
                response.raise_for_status()
            except httpx.RequestError as e:
                msg = f"An error occurred while requesting {e.request.url!r}."
                raise DeezerError(msg) from e
            except httpx.HTTPStatusError as e:
                msg = (
                    f"Error response {e.response.status_code} "
                    f"while requesting {e.request.url!r}."
                )
                raise DeezerError(msg) from e

            data = response.json().get("data", [])
            if not data:
                msg = "No data found in the response."
                raise DeezerError(msg)

            return data[0]

    async def get_artist(self, artist_name: str) -> DeezerArtist:
        params = {
            "q": artist_name,
            "limit": 1,
        }
        data = await self._request("search/artist", params)

        if data.get("type") == "artist":
            image_url = data.get("picture_xl") or data.get("cover_xl")
            if not image_url:
                msg = "No image found for the artist."
                raise DeezerError(msg)

            image_data = {"url": image_url}
            image = DeezerImage.model_validate(image_data)

            artist_data = {
                "id": data["id"],
                "name": data["name"],
                "image": image,
            }
            return DeezerArtist.model_validate(artist_data)

        msg = "No artist found."
        raise DeezerError(msg)
