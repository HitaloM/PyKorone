# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from typing import Any, TypeVar, get_args, overload

import httpx
from pydantic import BaseModel

from .types import DeezerData

T = TypeVar("T")


class DeezerError(Exception):
    pass


class DeezerClient:
    __slots__ = ("base_url",)

    def __init__(self):
        self.base_url = "https://api.deezer.com/"

    async def _request(self, endpoint: str, params: dict[str, str]) -> dict[str, Any]:
        response = None
        try:
            async with httpx.AsyncClient(http2=True, timeout=20) as client:
                response = await client.get(f"{self.base_url}{endpoint}", params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as http_error:
            error_message = "API request failed"
            if response:
                try:
                    error_json = response.json()
                    detailed_error_message = error_json.get("error", {}).get(
                        "message", "Unknown error"
                    )
                    error_message = f"API request failed: {detailed_error_message}"
                except ValueError:
                    pass
            raise DeezerError(error_message) from http_error

    @overload
    @staticmethod
    def _handle_key_error(data: dict[str, Any], key: str, model: type[T]) -> T: ...

    @overload
    @staticmethod
    def _handle_key_error(data: dict[str, Any], key: str, model: type[list[T]]) -> list[T]: ...

    @staticmethod
    def _handle_key_error(data: dict[str, Any], key: str, model: type[Any]) -> Any:
        try:
            value = data[key]
            model_args = get_args(model)
            if model_args and issubclass(model_args[0], BaseModel):
                return [model_args[0].model_validate(item) for item in value]
            if issubclass(model, BaseModel):
                return model.model_validate(data)
            msg = f"Unsupported model type: {model}"
            raise TypeError(msg)
        except KeyError as e:
            msg = f"Missing key in response data: {e}"
            raise DeezerError(msg) from e

    async def get_artist(self, artist_name: str) -> DeezerData:
        params = {
            "q": artist_name,
            "limit": 1,
        }
        response_data = await self._request("search/artist", params)

        if response_data["data"]:
            artist_info = response_data["data"][0]
            if artist_info.get("type") == "artist":
                image_url = artist_info.get("picture")
                if not image_url:
                    msg = "No image found for the artist."
                    raise DeezerError(msg)

                return self._handle_key_error(artist_info, "id", DeezerData)

        msg = "No artist found."
        raise DeezerError(msg)
