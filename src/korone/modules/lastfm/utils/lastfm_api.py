# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M.

from enum import StrEnum
from typing import Any, TypeVar, cast

import httpx
from pydantic import BaseModel

from korone.config import ConfigManager
from korone.utils.logging import get_logger

from .errors import ERROR_CODE_MAP, LastFMError
from .types import LastFMAlbum, LastFMArtist, LastFMTrack, LastFMUser

logger = get_logger(__name__)

API_KEY: str = ConfigManager.get("korone", "LASTFM_KEY")


class TimePeriod(StrEnum):
    OneWeek = "1 week"
    OneMonth = "1 month"
    ThreeMonths = "3 months"
    SixMonths = "6 months"
    OneYear = "1 year"
    AllTime = "All time"


T = TypeVar("T", bound=BaseModel)


class LastFMClient:
    __slots__ = ("api_key", "base_url")

    def __init__(self, api_key: str = API_KEY):
        self.api_key = api_key
        self.base_url = "https://ws.audioscrobbler.com/2.0"

    async def _request(self, params: dict[str, Any]) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(http2=True, timeout=20) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()

                if not response.content or response.content.strip() == b"":
                    logger.warning(
                        "Empty response from Last.fm API for method: %s",
                        params.get("method", "unknown"),
                    )
                    msg = "Empty response from Last.fm API"
                    raise LastFMError(msg)

                try:
                    return response.json()
                except ValueError as json_error:
                    logger.error(
                        "Invalid JSON response from Last.fm API for method: %s, response: %s",
                        params.get("method", "unknown"),
                        response.text[:100],
                    )
                    msg = f"Invalid JSON response from Last.fm API: {response.text[:100]}"
                    raise LastFMError(msg) from json_error

        except httpx.HTTPStatusError as e:
            error_message = "API request failed"
            try:
                if e.response.content and e.response.content.strip():
                    error_json = e.response.json()
                    error_message = (
                        f"API request failed: {error_json.get('message', 'Unknown error')}"
                    )
                    error_code = error_json.get("error")
                    error_class = ERROR_CODE_MAP.get(error_code, LastFMError)
                    raise error_class(error_message, error_code, e.response) from e
                logger.warning(
                    "API request failed with empty response (HTTP %s) for method: %s",
                    e.response.status_code,
                    params.get("method", "unknown"),
                )
                error_message = (
                    f"API request failed with empty response (HTTP {e.response.status_code})"
                )
                raise LastFMError(error_message) from e
            except ValueError:
                logger.error(
                    "API request failed while parsing error response (HTTP %s): %s",
                    e.response.status_code,
                    e,
                )
                raise LastFMError(error_message) from e
        except httpx.RequestError as e:
            if isinstance(e, httpx.TimeoutException):
                logger.warning(
                    "Request timeout for Last.fm API method: %s", params.get("method", "unknown")
                )
                msg = "Request timeout occurred"
            else:
                logger.error(
                    "Request error occurred for Last.fm API method: %s, error: %s",
                    params.get("method", "unknown"),
                    e,
                )
                msg = "Request error occurred"
            raise LastFMError(msg) from e

    @staticmethod
    def _time_period_to_api_string(duration: TimePeriod) -> str:
        period_map = {
            TimePeriod.OneWeek: "7day",
            TimePeriod.OneMonth: "1month",
            TimePeriod.ThreeMonths: "3month",
            TimePeriod.SixMonths: "6month",
            TimePeriod.OneYear: "12month",
            TimePeriod.AllTime: "overall",
        }
        return period_map[duration]

    def _build_params(self, method: str, user: str, **kwargs: Any) -> dict[str, Any]:
        return {
            "method": method,
            "user": user,
            "api_key": self.api_key,
            "format": "json",
            **kwargs,
        }

    @staticmethod
    def _handle_key_error(data: dict[str, Any], key: str, model: type[T]) -> list[T] | T:
        try:
            value = data[key]
            if isinstance(value, list):
                return [model.model_validate(item) for item in value]
            return model.model_validate(value)
        except KeyError as e:
            msg = f"Missing key in response data: {e}"
            raise LastFMError(msg) from e

    async def get_recent_tracks(
        self, username: str, limit: int = 5, extended: int = 1
    ) -> list[LastFMTrack]:
        params = self._build_params(
            "user.getrecenttracks", username, limit=limit, extended=extended
        )
        data = await self._request(params)
        return cast(
            list[LastFMTrack], self._handle_key_error(data["recenttracks"], "track", LastFMTrack)
        )

    async def get_user_info(self, username: str) -> LastFMUser:
        params = self._build_params("user.getInfo", username)
        data = await self._request(params)
        return cast(LastFMUser, self._handle_key_error(data, "user", LastFMUser))

    async def get_track_info(self, artist: str, track: str, username: str) -> LastFMTrack:
        params = self._build_params("track.getInfo", username, artist=artist, track=track)
        data = await self._request(params)
        return cast(LastFMTrack, self._handle_key_error(data, "track", LastFMTrack))

    async def get_album_info(self, artist: str, album: str, username: str) -> LastFMAlbum:
        params = self._build_params("album.getInfo", username, artist=artist, album=album)
        data = await self._request(params)
        return cast(LastFMAlbum, self._handle_key_error(data, "album", LastFMAlbum))

    async def get_artist_info(self, artist: str, username: str) -> LastFMArtist:
        params = self._build_params("artist.getInfo", username, artist=artist)
        data = await self._request(params)
        return cast(LastFMArtist, self._handle_key_error(data, "artist", LastFMArtist))

    async def get_top_albums(
        self, user: str, period: TimePeriod, limit: int = 9
    ) -> list[LastFMAlbum]:
        duration_str = self._time_period_to_api_string(period)
        params = self._build_params("user.gettopalbums", user, period=duration_str, limit=limit)
        data = await self._request(params)
        return cast(
            list[LastFMAlbum], self._handle_key_error(data["topalbums"], "album", LastFMAlbum)
        )

    async def get_top_tracks(
        self, user: str, period: TimePeriod = TimePeriod.AllTime, limit: int = 9
    ) -> list[LastFMTrack]:
        duration_str = self._time_period_to_api_string(period)
        params = self._build_params("user.gettoptracks", user, period=duration_str, limit=limit)
        data = await self._request(params)
        return cast(
            list[LastFMTrack], self._handle_key_error(data["toptracks"], "track", LastFMTrack)
        )

    async def get_top_artists(
        self, user: str, period: TimePeriod = TimePeriod.AllTime, limit: int = 9
    ) -> list[LastFMArtist]:
        duration_str = self._time_period_to_api_string(period)
        params = self._build_params("user.gettopartists", user, period=duration_str, limit=limit)
        data = await self._request(params)
        return cast(
            list[LastFMArtist], self._handle_key_error(data["topartists"], "artist", LastFMArtist)
        )
