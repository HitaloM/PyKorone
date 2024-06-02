# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import urllib.parse
from dataclasses import dataclass

import httpx

from korone.config import ConfigManager

API_KEY: str = ConfigManager.get("korone", "LASTFM_KEY")


@dataclass(slots=True, frozen=True)
class Image:
    size: str
    url: str

    @classmethod
    def from_dict(cls, data: dict):
        return cls(size=data["size"], url=data["#text"])


@dataclass(slots=True, frozen=True)
class Track:
    artist: str
    name: str
    album: str
    loved: int
    images: list[Image]
    now_playing: bool
    playcount: int
    played_at: int

    @classmethod
    def from_dict(cls, data: dict):
        images = [Image.from_dict(img) for img in data.get("image", [])]
        loved = int(data.get("userloved", 0))
        now_playing = (
            data["@attr"]["nowplaying"] == "true"
            if "@attr" in data and "nowplaying" in data["@attr"]
            else False
        )
        playcount = int(data.get("userplaycount", 0))
        played_at = int(data["date"]["uts"]) if "date" in data else 0
        album = data.get("album", {}).get("#text") or data.get("album", {}).get("title", "")
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
class User:
    username: str
    realname: str
    playcount: int
    registered: str
    images: list[Image]

    @classmethod
    def from_dict(cls, data: dict):
        images = [Image.from_dict(img) for img in data["image"]]
        return cls(
            username=data["name"],
            realname=data["realname"],
            playcount=int(data["playcount"]),
            registered=data["registered"]["unixtime"],
            images=images,
        )


@dataclass(slots=True, frozen=True)
class Album:
    artist: str
    name: str
    playcount: int
    images: list[Image]

    @classmethod
    def from_dict(cls, data: dict):
        images = [Image.from_dict(img) for img in data["image"]]
        return cls(
            artist=data["artist"],
            name=data["name"],
            playcount=int(data["userplaycount"]),
            images=images,
        )


@dataclass(slots=True, frozen=True)
class Artist:
    name: str
    playcount: int

    @classmethod
    def from_dict(cls, data: dict):
        return cls(name=data["name"], playcount=int(data["stats"]["userplaycount"]))


class LastFMClient:
    __slots__ = ("api_key", "base_url")

    def __init__(self, api_key: str = API_KEY):
        self.api_key = api_key
        self.base_url = "https://ws.audioscrobbler.com/2.0"

    async def _request(self, params: dict) -> dict:
        async with httpx.AsyncClient(http2=True) as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()

    async def get_recent_tracks(
        self, username: str, limit: int = 5, extended: int = 1
    ) -> list[Track]:
        params = {
            "method": "user.getrecenttracks",
            "user": username,
            "limit": limit,
            "extended": extended,
            "api_key": self.api_key,
            "format": "json",
        }
        data = await self._request(params)
        return [Track.from_dict(track) for track in data["recenttracks"]["track"]]

    async def get_user_info(self, username: str) -> User:
        params = {
            "method": "user.getinfo",
            "user": username,
            "api_key": self.api_key,
            "format": "json",
        }
        data = await self._request(params)
        return User.from_dict(data["user"])

    async def get_track_info(self, artist: str, track: str, username: str) -> Track:
        params = {
            "method": "track.getinfo",
            "artist": urllib.parse.quote(artist),
            "track": urllib.parse.quote(track),
            "user": username,
            "api_key": self.api_key,
            "format": "json",
        }
        data = await self._request(params)
        return Track.from_dict(data["track"])

    async def get_album_info(self, artist: str, album: str, username: str) -> Album:
        params = {
            "method": "album.getinfo",
            "artist": urllib.parse.quote(artist),
            "album": urllib.parse.quote(album),
            "user": username,
            "api_key": self.api_key,
            "format": "json",
        }
        data = await self._request(params)
        return Album.from_dict(data["album"])

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
