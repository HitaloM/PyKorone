from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HifiTrack:
    id: int
    title: str
    artist: str
    album: str | None = None
    album_cover_id: str | None = None
    duration: int | None = None
    explicit: bool = False
    audio_quality: str | None = None


@dataclass(frozen=True, slots=True)
class HifiSearchSession:
    user_id: int
    query: str
    tracks: list[HifiTrack]


@dataclass(frozen=True, slots=True)
class HifiTrackStream:
    url: str
    audio_quality: str | None
    mime_type: str | None
    codec: str | None
    requested_quality: str
