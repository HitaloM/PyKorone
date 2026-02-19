from __future__ import annotations

import secrets

import orjson

from korone import aredis

from .types import HifiSearchSession, HifiTrack

SESSION_TTL_SECONDS = 60 * 60
SESSION_KEY_PREFIX = "hifi:session:"


def _session_key(token: str) -> str:
    return f"{SESSION_KEY_PREFIX}{token}"


def _parse_track(item: object) -> HifiTrack | None:
    if not isinstance(item, dict):
        return None

    track_id = item.get("i")
    title = item.get("t")
    artist = item.get("a")
    album = item.get("al")
    album_cover_id = item.get("c")
    duration = item.get("d")
    explicit = item.get("e")
    quality = item.get("q")

    if isinstance(track_id, bool) or not isinstance(track_id, int):
        return None
    if not isinstance(title, str) or not title.strip():
        return None
    if not isinstance(artist, str) or not artist.strip():
        return None
    if album is not None and not isinstance(album, str):
        return None
    if album_cover_id is not None and not isinstance(album_cover_id, str):
        return None
    if isinstance(duration, bool):
        return None
    if duration is not None and not isinstance(duration, int):
        return None
    if not isinstance(explicit, bool):
        return None
    if quality is not None and not isinstance(quality, str):
        return None

    return HifiTrack(
        id=track_id,
        title=title,
        artist=artist,
        album=album,
        album_cover_id=album_cover_id,
        duration=duration,
        explicit=explicit,
        audio_quality=quality,
    )


async def create_search_session(query: str, tracks: list[HifiTrack]) -> str:
    token = secrets.token_hex(6)
    payload = {
        "q": query,
        "t": [
            {
                "i": track.id,
                "t": track.title,
                "a": track.artist,
                "al": track.album,
                "c": track.album_cover_id,
                "d": track.duration,
                "e": track.explicit,
                "q": track.audio_quality,
            }
            for track in tracks
        ],
    }
    await aredis.set(_session_key(token), orjson.dumps(payload), ex=SESSION_TTL_SECONDS)
    return token


async def get_search_session(token: str) -> HifiSearchSession | None:
    raw_payload = await aredis.get(_session_key(token))
    if raw_payload is None:
        return None

    try:
        payload = orjson.loads(raw_payload)
    except orjson.JSONDecodeError:
        return None

    if not isinstance(payload, dict):
        return None

    query = payload.get("q")
    raw_tracks = payload.get("t")
    if not isinstance(query, str) or not isinstance(raw_tracks, list):
        return None

    tracks: list[HifiTrack] = []
    for item in raw_tracks:
        track = _parse_track(item)
        if track is None:
            return None
        tracks.append(track)

    return HifiSearchSession(query=query, tracks=tracks)
