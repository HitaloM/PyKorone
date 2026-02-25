from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class LastFMTopAlbum:
    name: str
    artist: str
    playcount: int
    image_url: str | None


@dataclass(slots=True, frozen=True)
class LastFMTopArtist:
    name: str
    playcount: int


@dataclass(slots=True, frozen=True)
class LastFMRecentTrack:
    name: str
    artist: str
    album: str | None
    image_url: str | None
    now_playing: bool
    played_at: int | None
    loved: bool


@dataclass(slots=True, frozen=True)
class LastFMTrackInfo:
    user_playcount: int
    listeners: int
    playcount: int
    duration_ms: int | None
    tags: tuple[str, ...]


@dataclass(slots=True, frozen=True)
class LastFMArtistInfo:
    name: str
    user_playcount: int
    listeners: int
    playcount: int
    tags: tuple[str, ...]


@dataclass(slots=True, frozen=True)
class LastFMAlbumInfo:
    name: str
    artist: str
    user_playcount: int
    listeners: int
    playcount: int
    track_count: int
    tags: tuple[str, ...]
    image_url: str | None
