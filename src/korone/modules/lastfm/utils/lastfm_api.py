# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M.

from enum import StrEnum
from typing import Any

import httpx
from pydantic import BaseModel

from korone.config import ConfigManager

from .errors import ERROR_CODE_MAP, LastFMError
from .types import LastFMAlbum, LastFMArtist, LastFMTrack, LastFMUser

API_KEY: str = ConfigManager.get("korone", "LASTFM_KEY")


class TimePeriod(StrEnum):
    OneWeek = "1 week"
    OneMonth = "1 month"
    ThreeMonths = "3 months"
    SixMonths = "6 months"
    OneYear = "1 year"
    AllTime = "All time"


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
                return response.json()
        except httpx.HTTPStatusError as e:
            error_message = "API request failed"
            try:
                error_json = response.json()
                error_message = f"API request failed: {error_json.get('message', 'Unknown error')}"
                error_code = error_json.get("error")
                error_class = ERROR_CODE_MAP.get(error_code, LastFMError)
                raise error_class(error_message, error_code, response) from e
            except ValueError:
                raise LastFMError(error_message) from e
        except httpx.RequestError as e:
            msg = "Request error occurred"
            raise LastFMError(msg) from e

    @staticmethod
    def _time_period_to_api_string(duration: TimePeriod) -> str:
        return {
            TimePeriod.OneWeek: "7day",
            TimePeriod.OneMonth: "1month",
            TimePeriod.ThreeMonths: "3month",
            TimePeriod.SixMonths: "6month",
            TimePeriod.OneYear: "12month",
            TimePeriod.AllTime: "overall",
        }[duration]

    @staticmethod
    def _build_params(method: str, user: str, **kwargs: Any) -> dict[str, Any]:
        return {
            "method": method,
            "user": user,
            "api_key": API_KEY,
            "format": "json",
        } | kwargs

    @staticmethod
    def _handle_key_error(data: dict[str, Any], key: str, model: type[BaseModel]) -> Any:
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
        return self._handle_key_error(data["recenttracks"], "track", LastFMTrack)

    async def get_user_info(self, username: str) -> LastFMUser:
        params = self._build_params("user.getInfo", username)
        data = await self._request(params)
        return self._handle_key_error(data, "user", LastFMUser)

    async def get_track_info(self, artist: str, track: str, username: str) -> LastFMTrack:
        params = self._build_params("track.getInfo", username, artist=artist, track=track)
        data = await self._request(params)
        return self._handle_key_error(data, "track", LastFMTrack)

    async def get_album_info(self, artist: str, album: str, username: str) -> LastFMAlbum:
        params = self._build_params("album.getInfo", username, artist=artist, album=album)
        data = await self._request(params)
        return self._handle_key_error(data, "album", LastFMAlbum)

    async def get_artist_info(self, artist: str, username: str) -> LastFMArtist:
        params = self._build_params("artist.getInfo", username, artist=artist)
        data = await self._request(params)
        return self._handle_key_error(data, "artist", LastFMArtist)

    async def get_top_albums(
        self, user: str, period: TimePeriod, limit: int = 9
    ) -> list[LastFMAlbum]:
        duration_str = self._time_period_to_api_string(period)
        params = self._build_params("user.gettopalbums", user, period=duration_str, limit=limit)
        data = await self._request(params)
        return self._handle_key_error(data["topalbums"], "album", LastFMAlbum)

    async def get_top_tracks(
        self, user: str, period: TimePeriod = TimePeriod.AllTime, limit: int = 9
    ) -> list[LastFMTrack]:
        duration_str = self._time_period_to_api_string(period)
        params = self._build_params("user.gettoptracks", user, period=duration_str, limit=limit)
        data = await self._request(params)
        return self._handle_key_error(data["toptracks"], "track", LastFMTrack)

    async def get_top_artists(
        self, user: str, period: TimePeriod = TimePeriod.AllTime, limit: int = 9
    ) -> list[LastFMArtist]:
        duration_str = self._time_period_to_api_string(period)
        params = self._build_params("user.gettopartists", user, period=duration_str, limit=limit)
        data = await self._request(params)
        return self._handle_key_error(data["topartists"], "artist", LastFMArtist)
