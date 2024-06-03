# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import urllib.parse
from dataclasses import dataclass
from enum import Enum

import httpx

from korone.config import ConfigManager

API_KEY: str = ConfigManager.get("korone", "LASTFM_KEY")


class TimePeriod(Enum):
    OneWeek = "1 week"
    OneMonth = "1 month"
    ThreeMonths = "3 months"
    SixMonths = "6 months"
    OneYear = "1 year"
    AllTime = "All time"


class LastFMError(Exception):
    pass


@dataclass(slots=True, frozen=True)
class LastFMImage:
    size: str
    url: str

    @classmethod
    def from_dict(cls, data: dict):
        return cls(size=data["size"], url=data["#text"])


@dataclass(slots=True, frozen=True)
class LastFMTrack:
    artist: str
    name: str
    album: str
    loved: int
    images: list[LastFMImage]
    now_playing: bool
    playcount: int
    played_at: int

    @classmethod
    def from_dict(cls, data: dict):
        images = [LastFMImage.from_dict(img) for img in data.get("image", []) if img.get("#text")]
        loved = int(data.get("userloved", 0))
        now_playing = (
            data["@attr"]["nowplaying"] == "true"
            if "@attr" in data and "nowplaying" in data["@attr"]
            else False
        )
        playcount = int(data.get("userplaycount", data.get("playcount", 0)))
        played_at = int(data.get("date", {}).get("uts", 0))
        album = data.get("album", {}).get("#text") if "album" in data else ""
        return cls(
            artist=data["artist"]["name"],
            name=data["name"],
            album=album,
            loved=loved,
            images=images,
            now_playing=now_playing,
            playcount=playcount,
            played_at=played_at,
        )


@dataclass(slots=True, frozen=True)
class LastFMUser:
    username: str
    realname: str
    playcount: int
    registered: str
    images: list[LastFMImage]

    @classmethod
    def from_dict(cls, data: dict):
        images = [LastFMImage.from_dict(img) for img in data["image"] if img.get("#text")]
        return cls(
            username=data["name"],
            realname=data["realname"],
            playcount=int(data["playcount"]),
            registered=data["registered"]["unixtime"],
            images=images,
        )


@dataclass(slots=True, frozen=True)
class LastFMAlbum:
    artist: str
    name: str
    playcount: int
    loved: int
    images: list[LastFMImage]

    @classmethod
    def from_dict(cls, data: dict):
        loved = int(data.get("userloved", 0))
        playcount = int(data.get("userplaycount", data.get("playcount", 0)))
        images = [LastFMImage.from_dict(img) for img in data["image"] if img.get("#text")]
        artist = data["artist"]["name"] if isinstance(data["artist"], dict) else data["artist"]
        return cls(
            artist=artist,
            name=data["name"],
            playcount=playcount,
            loved=loved,
            images=images,
        )


@dataclass(slots=True, frozen=True)
class Artist:
    name: str
    playcount: int
    loved: int
    images: list[LastFMImage]

    @classmethod
    def from_dict(cls, data: dict):
        loved = int(data.get("userloved", 0))
        playcount = int(data["stats"].get("userplaycount"))
        images = [LastFMImage.from_dict(img) for img in data.get("image", []) if img.get("#text")]
        return cls(
            name=data["name"],
            playcount=playcount,
            loved=loved,
            images=images,
        )


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
        return [LastFMTrack.from_dict(track) for track in data["recenttracks"]["track"]]

    async def get_user_info(self, username: str) -> LastFMUser:
        params = {
            "method": "user.getinfo",
            "user": username,
            "api_key": self.api_key,
            "format": "json",
        }
        data = await self._request(params)
        return LastFMUser.from_dict(data["user"])

    async def get_track_info(self, artist: str, track: str, username: str) -> LastFMTrack:
        params = {
            "method": "track.getinfo",
            "artist": urllib.parse.quote(artist),
            "track": urllib.parse.quote(track),
            "user": username,
            "api_key": self.api_key,
            "format": "json",
        }
        data = await self._request(params)
        return LastFMTrack.from_dict(data["track"])

    async def get_album_info(self, artist: str, album: str, username: str) -> LastFMAlbum:
        params = {
            "method": "album.getinfo",
            "artist": urllib.parse.quote(artist),
            "album": urllib.parse.quote(album),
            "user": username,
            "api_key": self.api_key,
            "format": "json",
        }
        data = await self._request(params)
        return LastFMAlbum.from_dict(data["album"])

    async def get_artist_info(self, artist: str, username: str) -> Artist:
        params = {
            "method": "artist.getinfo",
            "artist": urllib.parse.quote(artist),
            "user": username,
            "api_key": self.api_key,
            "format": "json",
        }
        data = await self._request(params)
        return Artist.from_dict(data["artist"])

    async def get_top_albums(
        self, user: str, period: str, limit: int = 9, page: int = 1
    ) -> list[LastFMAlbum]:
        duration_str = self._time_period_to_api_string(TimePeriod(period))
        params = {
            "method": "user.gettopalbums",
            "user": user,
            "period": duration_str,
            "limit": limit,
            "page": page,
            "api_key": self.api_key,
            "format": "json",
        }
        data = await self._request(params)
        return [LastFMAlbum.from_dict(album) for album in data["topalbums"]["album"]]

    async def get_top_tracks(
        self, user: str, period: str = "overall", limit: int = 9, page: int = 1
    ) -> list[LastFMTrack]:
        params = {
            "method": "user.gettoptracks",
            "user": user,
            "period": period,
            "limit": limit,
            "page": page,
            "api_key": self.api_key,
            "format": "json",
        }
        data = await self._request(params)
        return [LastFMTrack.from_dict(track) for track in data["toptracks"]["track"]]

    async def get_top_artists(
        self, user: str, period: str = "overall", limit: int = 9, page: int = 1
    ) -> list[Artist]:
        params = {
            "method": "user.gettopartists",
            "user": user,
            "period": period,
            "limit": limit,
            "page": page,
            "api_key": self.api_key,
            "format": "json",
        }
        data = await self._request(params)
        return [Artist.from_dict(artist) for artist in data["topartists"]["artist"]]