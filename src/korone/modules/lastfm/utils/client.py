from __future__ import annotations

import html
from typing import TYPE_CHECKING

import aiohttp
import orjson

from korone.config import CONFIG
from korone.utils.aiohttp_session import HTTPClient

from .errors import LastFMAPIError, LastFMConfigurationError, LastFMPayloadError, LastFMRequestError
from .types import (
    LastFMAlbumInfo,
    LastFMArtistInfo,
    LastFMRecentTrack,
    LastFMTopAlbum,
    LastFMTopArtist,
    LastFMTrackInfo,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

LASTFM_BASE_URL = "https://ws.audioscrobbler.com/2.0/"
LASTFM_TIMEOUT_SECONDS = 20
LASTFM_PLACEHOLDER_IMAGE = "2a96cbd8b46e442fc41c2b86b821562f"


def _as_dict(value: object) -> dict[str, object] | None:
    return value if isinstance(value, dict) else None


def _as_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _as_dict_nodes(value: object) -> list[dict[str, object]]:
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [node for node in value if isinstance(node, dict)]
    return []


def _as_non_empty_str(value: object) -> str | None:
    if isinstance(value, str):
        decoded = html.unescape(value).strip()
        if decoded:
            return decoded
    return None


def _as_int(value: object, *, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        value = value.strip()
        if value.isdigit():
            return int(value)
    return default


def _extract_name(node: object) -> str | None:
    if isinstance(node, str):
        return _as_non_empty_str(node)
    if not isinstance(node, dict):
        return None

    return _as_non_empty_str(node.get("#text")) or _as_non_empty_str(node.get("name"))


def _extract_now_playing(track: Mapping[str, object]) -> bool:
    attr = _as_dict(track.get("@attr"))
    if not attr:
        return False

    return str(attr.get("nowplaying", "")).lower() == "true"


def _extract_played_at(track: Mapping[str, object]) -> int | None:
    date_info = _as_dict(track.get("date"))
    if not date_info:
        return None

    uts = date_info.get("uts")
    if isinstance(uts, int):
        return uts
    if isinstance(uts, str) and uts.isdigit():
        return int(uts)
    return None


def _extract_loved(track: Mapping[str, object]) -> bool:
    loved = track.get("loved")
    if isinstance(loved, bool):
        return loved
    if isinstance(loved, int):
        return loved == 1
    if isinstance(loved, str):
        return loved.strip() == "1"
    return False


def _extract_best_image(track: Mapping[str, object]) -> str | None:
    images = _as_list(track.get("image"))
    for image in reversed(images):
        image_data = _as_dict(image)
        if not image_data:
            continue

        url = _as_non_empty_str(image_data.get("#text"))
        if not url or LASTFM_PLACEHOLDER_IMAGE in url:
            continue

        return url

    return None


def _extract_tags(payload: Mapping[str, object], *, key: str) -> tuple[str, ...]:
    tags_node = _as_dict(payload.get(key))
    if not tags_node:
        return ()

    raw_tags = tags_node.get("tag")
    if isinstance(raw_tags, dict):
        name = _extract_name(raw_tags)
        return (name,) if name else ()

    if not isinstance(raw_tags, list):
        return ()

    parsed: list[str] = []
    seen: set[str] = set()
    for item in raw_tags:
        item_data = _as_dict(item)
        if not item_data:
            continue

        tag_name = _extract_name(item_data)
        if not tag_name:
            continue

        normalized = tag_name.lower()
        if normalized in seen:
            continue

        seen.add(normalized)
        parsed.append(tag_name)

    return tuple(parsed)


def _extract_track_tags(track_payload: Mapping[str, object]) -> tuple[str, ...]:
    return _extract_tags(track_payload, key="toptags")


def _count_album_tracks(album_payload: Mapping[str, object]) -> int:
    tracks_wrapper = _as_dict(album_payload.get("tracks"))
    if not tracks_wrapper:
        return 0

    tracks = tracks_wrapper.get("track")
    if isinstance(tracks, list):
        return len(tracks)
    if isinstance(tracks, dict):
        return 1
    return 0


class LastFMClient:
    __slots__ = ("api_key", "base_url", "timeout")

    def __init__(self, api_key: str | None = None, base_url: str = LASTFM_BASE_URL) -> None:
        resolved_key = (api_key or CONFIG.lastfm_key or "").strip()
        if not resolved_key:
            msg = "Last.fm API key is not configured."
            raise LastFMConfigurationError(msg)

        self.api_key = resolved_key
        self.base_url = base_url
        self.timeout = aiohttp.ClientTimeout(total=LASTFM_TIMEOUT_SECONDS)

    async def _request(self, *, method: str, params: dict[str, str | int]) -> dict[str, object]:
        request_params: dict[str, str | int] = {"method": method, "api_key": self.api_key, "format": "json", **params}

        session = await HTTPClient.get_session()
        try:
            async with session.get(self.base_url, params=request_params, timeout=self.timeout) as response:
                payload: object
                try:
                    payload = await response.json(content_type=None, loads=orjson.loads)
                except (aiohttp.ContentTypeError, ValueError) as exc:
                    msg = "Last.fm returned an invalid JSON payload."
                    raise LastFMPayloadError(msg) from exc

                if not isinstance(payload, dict):
                    msg = "Last.fm returned an unexpected payload format."
                    raise LastFMPayloadError(msg)

                error_code = payload.get("error")
                if error_code is not None:
                    code = _as_int(error_code, default=0) or None
                    message = _as_non_empty_str(payload.get("message")) or "Last.fm API error."
                    raise LastFMAPIError(message, error_code=code)

                if response.status != 200:
                    msg = f"Last.fm request failed with status {response.status}."
                    raise LastFMRequestError(msg, status_code=response.status)

                return payload
        except TimeoutError as exc:
            msg = "Last.fm request timed out."
            raise LastFMRequestError(msg) from exc
        except aiohttp.ClientError as exc:
            msg = "Last.fm request failed."
            raise LastFMRequestError(msg) from exc

    async def get_recent_tracks(self, *, username: str, limit: int = 3) -> list[LastFMRecentTrack]:
        payload = await self._request(
            method="user.getrecenttracks", params={"user": username, "extended": 1, "limit": max(1, limit)}
        )
        recent_tracks = _as_dict(payload.get("recenttracks"))
        if not recent_tracks:
            return []

        tracks_nodes = _as_dict_nodes(recent_tracks.get("track"))
        if not tracks_nodes:
            return []

        parsed_tracks: list[LastFMRecentTrack] = []
        for track_node in tracks_nodes:
            name = _as_non_empty_str(track_node.get("name"))
            artist = _extract_name(track_node.get("artist"))
            if not name or not artist:
                continue

            parsed_tracks.append(
                LastFMRecentTrack(
                    name=name,
                    artist=artist,
                    album=_extract_name(track_node.get("album")),
                    image_url=_extract_best_image(track_node),
                    now_playing=_extract_now_playing(track_node),
                    played_at=_extract_played_at(track_node),
                    loved=_extract_loved(track_node),
                )
            )

        return parsed_tracks

    async def get_top_albums(self, *, username: str, period: str = "overall", limit: int = 9) -> list[LastFMTopAlbum]:
        payload = await self._request(
            method="user.gettopalbums", params={"user": username, "period": period, "limit": max(1, limit)}
        )

        top_albums_payload = _as_dict(payload.get("topalbums"))
        if not top_albums_payload:
            return []

        album_nodes = _as_dict_nodes(top_albums_payload.get("album"))
        if not album_nodes:
            return []

        albums: list[LastFMTopAlbum] = []
        for album_node in album_nodes:
            album_name = _as_non_empty_str(album_node.get("name"))
            album_artist = _extract_name(album_node.get("artist"))
            if not album_name or not album_artist:
                continue

            albums.append(
                LastFMTopAlbum(
                    name=album_name,
                    artist=album_artist,
                    playcount=_as_int(album_node.get("playcount")),
                    image_url=_extract_best_image(album_node),
                )
            )

        return albums

    async def get_top_artists(
        self, *, username: str, period: str = "overall", limit: int = 100
    ) -> list[LastFMTopArtist]:
        payload = await self._request(
            method="user.gettopartists", params={"user": username, "period": period, "limit": max(1, limit)}
        )

        top_artists_payload = _as_dict(payload.get("topartists"))
        if not top_artists_payload:
            return []

        artist_nodes = _as_dict_nodes(top_artists_payload.get("artist"))
        if not artist_nodes:
            return []

        artists: list[LastFMTopArtist] = []
        for artist_node in artist_nodes:
            artist_name = _as_non_empty_str(artist_node.get("name"))
            if not artist_name:
                continue

            artists.append(LastFMTopArtist(name=artist_name, playcount=_as_int(artist_node.get("playcount"))))

        return artists

    async def get_track_info(self, *, username: str, artist: str, track: str) -> LastFMTrackInfo | None:
        payload = await self._request(
            method="track.getInfo", params={"artist": artist, "track": track, "username": username}
        )

        track_payload = _as_dict(payload.get("track"))
        if not track_payload:
            return None

        return LastFMTrackInfo(
            user_playcount=_as_int(track_payload.get("userplaycount")),
            listeners=_as_int(track_payload.get("listeners")),
            playcount=_as_int(track_payload.get("playcount")),
            duration_ms=_as_int(track_payload.get("duration")) or None,
            tags=_extract_track_tags(track_payload),
        )

    async def get_artist_info(self, *, username: str, artist: str) -> LastFMArtistInfo | None:
        payload = await self._request(method="artist.getInfo", params={"artist": artist, "username": username})

        artist_payload = _as_dict(payload.get("artist"))
        if not artist_payload:
            return None

        stats = _as_dict(artist_payload.get("stats"))
        listeners = _as_int(stats.get("listeners")) if stats else 0
        playcount = _as_int(stats.get("playcount")) if stats else 0
        user_playcount = _as_int(stats.get("userplaycount")) if stats else 0

        artist_name = _as_non_empty_str(artist_payload.get("name")) or artist
        return LastFMArtistInfo(
            name=artist_name,
            user_playcount=user_playcount,
            listeners=listeners,
            playcount=playcount,
            tags=_extract_tags(artist_payload, key="tags"),
        )

    async def get_album_info(self, *, username: str, artist: str, album: str) -> LastFMAlbumInfo | None:
        payload = await self._request(
            method="album.getInfo", params={"artist": artist, "album": album, "username": username}
        )

        album_payload = _as_dict(payload.get("album"))
        if not album_payload:
            return None

        album_name = _as_non_empty_str(album_payload.get("name")) or album
        album_artist = _extract_name(album_payload.get("artist")) or artist

        return LastFMAlbumInfo(
            name=album_name,
            artist=album_artist,
            user_playcount=_as_int(album_payload.get("userplaycount")),
            listeners=_as_int(album_payload.get("listeners")),
            playcount=_as_int(album_payload.get("playcount")),
            track_count=_count_album_tracks(album_payload),
            tags=_extract_tags(album_payload, key="tags"),
            image_url=_extract_best_image(album_payload),
        )

    async def user_exists(self, *, username: str) -> bool:
        try:
            payload = await self._request(method="user.getInfo", params={"user": username})
        except LastFMAPIError as exc:
            if exc.error_code == 6:
                return False
            raise

        user_payload = _as_dict(payload.get("user"))
        if not user_payload:
            return False

        return _as_non_empty_str(user_payload.get("name")) is not None
