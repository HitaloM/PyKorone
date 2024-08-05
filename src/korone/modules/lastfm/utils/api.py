# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from enum import Enum

import httpx

from korone.config import ConfigManager
from korone.modules.lastfm.utils.types import LastFMAlbum, LastFMArtist, LastFMTrack, LastFMUser

API_KEY: str = ConfigManager.get("korone", "LASTFM_KEY")


class LastFMError(Exception):
    pass


class TimePeriod(Enum):
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

    async def _request(self, params: dict) -> dict:
        async with httpx.AsyncClient(http2=True, timeout=20) as client:
            response = await client.get(self.base_url, params=params)
            if response.status_code != 200:
                msg = response.json().get("message")
                raise LastFMError(msg)
            return response.json()

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

    async def get_recent_tracks(
        self, username: str, limit: int = 5, extended: int = 1
    ) -> list[LastFMTrack]:
        params = {
            "method": "user.getrecenttracks",
            "user": username,
            "limit": limit,
            "extended": extended,
            "api_key": self.api_key,
            "format": "json",
        }
        data = await self._request(params)
        return [LastFMTrack.model_validate(track) for track in data["recenttracks"]["track"]]

    async def get_user_info(self, username: str) -> LastFMUser:
        params = {
            "method": "user.getinfo",
            "user": username,
            "api_key": self.api_key,
            "format": "json",
        }
        data = await self._request(params)
        return LastFMUser.model_validate(data["user"])

    async def get_track_info(self, artist: str, track: str, username: str) -> LastFMTrack:
        params = {
            "method": "track.getinfo",
            "artist": artist,
            "track": track,
            "user": username,
            "api_key": self.api_key,
            "format": "json",
        }
        data = await self._request(params)
        return LastFMTrack.model_validate(data["track"])

    async def get_album_info(self, artist: str, album: str, username: str) -> LastFMAlbum:
        params = {
            "method": "album.getinfo",
            "artist": artist,
            "album": album,
            "user": username,
            "api_key": self.api_key,
            "format": "json",
        }
        data = await self._request(params)
        return LastFMAlbum.model_validate(data["album"])

    async def get_artist_info(self, artist: str, username: str) -> LastFMArtist:
        params = {
            "method": "artist.getinfo",
            "artist": artist,
            "user": username,
            "api_key": self.api_key,
            "format": "json",
        }
        data = await self._request(params)
        return LastFMArtist.model_validate(data["artist"])

    async def get_top_albums(self, user: str, period: str, limit: int = 9) -> list[LastFMAlbum]:
        duration_str = self._time_period_to_api_string(TimePeriod(period))
        params = {
            "method": "user.gettopalbums",
            "user": user,
            "period": duration_str,
            "limit": limit,
            "api_key": self.api_key,
            "format": "json",
        }
        data = await self._request(params)
        return [LastFMAlbum.model_validate(album) for album in data["topalbums"]["album"]]

    async def get_top_tracks(
        self, user: str, period: str = "overall", limit: int = 9
    ) -> list[LastFMTrack]:
        duration_str = self._time_period_to_api_string(TimePeriod(period))
        params = {
            "method": "user.gettoptracks",
            "user": user,
            "period": duration_str,
            "limit": limit,
            "api_key": self.api_key,
            "format": "json",
        }
        data = await self._request(params)
        return [LastFMTrack.model_validate(track) for track in data["toptracks"]["track"]]

    async def get_top_artists(
        self, user: str, period: str = "overall", limit: int = 9
    ) -> list[LastFMArtist]:
        duration_str = self._time_period_to_api_string(TimePeriod(period))
        params = {
            "method": "user.gettopartists",
            "user": user,
            "period": duration_str,
            "limit": limit,
            "api_key": self.api_key,
            "format": "json",
        }
        data = await self._request(params)
        return [LastFMArtist.model_validate(artist) for artist in data["topartists"]["artist"]]
