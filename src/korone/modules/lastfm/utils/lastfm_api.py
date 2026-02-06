from __future__ import annotations

from enum import StrEnum
from typing import Any, ClassVar, TypeVar, cast

import aiohttp
from pydantic import BaseModel

from korone.config import CONFIG
from korone.logger import get_logger

from .errors import ERROR_CODE_MAP, LastFMError
from .types import LastFMAlbum, LastFMArtist, LastFMTrack, LastFMUser

logger = get_logger(__name__)


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

    _period_map: ClassVar[dict[TimePeriod, str]] = {
        TimePeriod.OneWeek: "7day",
        TimePeriod.OneMonth: "1month",
        TimePeriod.ThreeMonths: "3month",
        TimePeriod.SixMonths: "6month",
        TimePeriod.OneYear: "12month",
        TimePeriod.AllTime: "overall",
    }
    _timeout = aiohttp.ClientTimeout(total=20)

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or CONFIG.lastfm_key
        self.base_url = "https://ws.audioscrobbler.com/2.0"

        if not self.api_key:
            msg = "Last.fm API key is not configured"
            raise LastFMError(msg)

    async def _request(self, params: dict[str, Any]) -> dict[str, Any]:
        try:
            async with (
                aiohttp.ClientSession(timeout=self._timeout) as session,
                session.get(self.base_url, params=params) as response,
            ):
                if response.status >= 400:
                    await LastFMClient._raise_http_error(response, params)

                data = await response.json()
                if not data:
                    msg = "Empty response from Last.fm API"
                    raise LastFMError(msg)

                if "error" in data:
                    error_code = data.get("error")
                    error_message = data.get("message", "Unknown error")
                    error_class = ERROR_CODE_MAP.get(error_code, LastFMError)
                    msg = f"API request failed: {error_message}"
                    raise error_class(msg, error_code, response)

                return data
        except aiohttp.ClientResponseError as exc:
            msg = f"API request failed with status code {exc.status}"
            raise LastFMError(msg) from exc
        except aiohttp.ClientError as exc:
            msg = "Request error occurred"
            raise LastFMError(msg) from exc
        except ValueError as exc:
            msg = "Invalid JSON response from Last.fm API"
            raise LastFMError(msg) from exc

    @staticmethod
    async def _raise_http_error(response: aiohttp.ClientResponse, params: dict[str, Any]) -> None:
        try:
            data = await response.json()
            error_code = data.get("error")
            error_message = data.get("message", "Unknown error")
            error_class = ERROR_CODE_MAP.get(error_code, LastFMError)
            msg = f"API request failed: {error_message}"
            raise error_class(msg, error_code, response)
        except ValueError:
            logger.warning(
                "API request failed with empty response (HTTP %s) for method: %s",
                response.status,
                params.get("method", "unknown"),
            )
            msg = f"API request failed with empty response (HTTP {response.status})"
            raise LastFMError(msg) from None

    @staticmethod
    def _time_period_to_api_string(duration: TimePeriod) -> str:
        return LastFMClient._period_map[duration]

    def _build_params(self, method: str, user: str, **kwargs: str | int) -> dict[str, Any]:
        return {"method": method, "user": user, "api_key": self.api_key, "format": "json", **kwargs}

    @staticmethod
    def _handle_key_error(data: dict[str, Any], key: str, model: type[T]) -> list[T] | T:
        try:
            value = data[key]
            if isinstance(value, list):
                return [model.model_validate(item) for item in value]
            return model.model_validate(value)
        except KeyError as exc:
            msg = f"Missing key in response data: {exc}"
            raise LastFMError(msg) from exc

    async def get_recent_tracks(self, username: str, limit: int = 5, extended: int = 1) -> list[LastFMTrack]:
        params = self._build_params("user.getrecenttracks", username, limit=limit, extended=extended)
        data = await self._request(params)
        raw_tracks = self._handle_key_error(data["recenttracks"], "track", LastFMTrack)
        if isinstance(raw_tracks, LastFMTrack):
            return [raw_tracks]
        return raw_tracks

    async def get_user_info(self, username: str) -> LastFMUser:
        params = self._build_params("user.getInfo", username)
        data = await self._request(params)
        return cast("LastFMUser", self._handle_key_error(data, "user", LastFMUser))

    async def get_track_info(self, artist: str, track: str, username: str | None = None) -> LastFMTrack:
        params = {
            "method": "track.getInfo",
            "api_key": self.api_key,
            "format": "json",
            "artist": artist,
            "track": track,
        }
        if username:
            params["username"] = username
        data = await self._request(params)
        return cast("LastFMTrack", self._handle_key_error(data, "track", LastFMTrack))

    async def get_album_info(self, artist: str, album: str, username: str | None = None) -> LastFMAlbum:
        params = {
            "method": "album.getInfo",
            "api_key": self.api_key,
            "format": "json",
            "artist": artist,
            "album": album,
        }
        if username:
            params["username"] = username
        data = await self._request(params)
        return cast("LastFMAlbum", self._handle_key_error(data, "album", LastFMAlbum))

    async def get_artist_info(self, artist: str, username: str | None = None) -> LastFMArtist:
        params = {"method": "artist.getInfo", "api_key": self.api_key, "format": "json", "artist": artist}
        if username:
            params["username"] = username
        data = await self._request(params)
        return cast("LastFMArtist", self._handle_key_error(data, "artist", LastFMArtist))

    async def get_top_albums(self, user: str, period: TimePeriod, limit: int = 9) -> list[LastFMAlbum]:
        duration_str = self._time_period_to_api_string(period)
        params = self._build_params("user.gettopalbums", user, period=duration_str, limit=limit)
        data = await self._request(params)
        return cast("list[LastFMAlbum]", self._handle_key_error(data["topalbums"], "album", LastFMAlbum))

    async def get_top_tracks(
        self, user: str, period: TimePeriod = TimePeriod.AllTime, limit: int = 9
    ) -> list[LastFMTrack]:
        duration_str = self._time_period_to_api_string(period)
        params = self._build_params("user.gettoptracks", user, period=duration_str, limit=limit)
        data = await self._request(params)
        return cast("list[LastFMTrack]", self._handle_key_error(data["toptracks"], "track", LastFMTrack))

    async def get_top_artists(
        self, user: str, period: TimePeriod = TimePeriod.AllTime, limit: int = 9
    ) -> list[LastFMArtist]:
        duration_str = self._time_period_to_api_string(period)
        params = self._build_params("user.gettopartists", user, period=duration_str, limit=limit)
        data = await self._request(params)
        return cast("list[LastFMArtist]", self._handle_key_error(data["topartists"], "artist", LastFMArtist))
