from __future__ import annotations

import aiohttp
import orjson

from korone.utils.aiohttp_session import HTTPClient

DEEZER_BASE_URL = "https://api.deezer.com"
DEEZER_TIMEOUT_SECONDS = 12
DEEZER_ARTIST_IMAGE_KEYS = ("picture_xl", "picture_big", "picture_medium", "picture_small", "picture")
DEEZER_COVER_IMAGE_KEYS = ("cover_xl", "cover_big", "cover_medium", "cover_small", "cover")


def _as_dict(value: object) -> dict[str, object] | None:
    return value if isinstance(value, dict) else None


def _as_non_empty_str(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _normalize_query_value(value: str) -> str:
    return " ".join(value.replace('"', " ").split())


def _build_query(*, artist: str | None = None, track: str | None = None, album: str | None = None) -> str:
    parts: list[str] = []
    if artist:
        artist_value = _normalize_query_value(artist)
        if artist_value:
            parts.append(f'artist:"{artist_value}"')
    if track:
        track_value = _normalize_query_value(track)
        if track_value:
            parts.append(f'track:"{track_value}"')
    if album:
        album_value = _normalize_query_value(album)
        if album_value:
            parts.append(f'album:"{album_value}"')

    return " ".join(parts)


def _extract_image_url(node: dict[str, object], *, keys: tuple[str, ...]) -> str | None:
    for key in keys:
        image_url = _as_non_empty_str(node.get(key))
        if image_url:
            return image_url

    return None


class DeezerError(Exception):
    """Raised when Deezer requests fail."""


class DeezerClient:
    __slots__ = ("base_url", "timeout")

    def __init__(self, base_url: str = DEEZER_BASE_URL) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=DEEZER_TIMEOUT_SECONDS)

    async def _request(self, path: str, *, params: dict[str, str | int]) -> dict[str, object]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        session = await HTTPClient.get_session()

        try:
            async with session.get(url, params=params, timeout=self.timeout) as response:
                if response.status != 200:
                    msg = f"Deezer request failed with status {response.status}."
                    raise DeezerError(msg)

                try:
                    payload = await response.json(content_type=None, loads=orjson.loads)
                except (aiohttp.ContentTypeError, ValueError) as exc:
                    msg = "Deezer returned an invalid payload."
                    raise DeezerError(msg) from exc
        except TimeoutError as exc:
            msg = "Deezer request timed out."
            raise DeezerError(msg) from exc
        except aiohttp.ClientError as exc:
            msg = "Deezer request failed."
            raise DeezerError(msg) from exc

        if not isinstance(payload, dict):
            msg = "Deezer returned an unexpected payload format."
            raise DeezerError(msg)

        return payload

    @staticmethod
    def _first_data_node(payload: dict[str, object]) -> dict[str, object] | None:
        raw_items = payload.get("data")
        if not isinstance(raw_items, list) or not raw_items:
            return None

        return _as_dict(raw_items[0])

    async def get_artist_image(self, artist_name: str) -> str | None:
        payload = await self._request("search/artist", params={"q": artist_name, "limit": 1})
        artist_node = self._first_data_node(payload)
        if not artist_node:
            return None

        return _extract_image_url(artist_node, keys=DEEZER_ARTIST_IMAGE_KEYS)

    async def get_track_album_image(self, *, artist_name: str, track_name: str) -> str | None:
        query = _build_query(artist=artist_name, track=track_name)
        if not query:
            return None

        payload = await self._request("search", params={"q": query, "limit": 1})
        track_node = self._first_data_node(payload)
        if not track_node:
            return None

        album_node = _as_dict(track_node.get("album"))
        if album_node:
            image_url = _extract_image_url(album_node, keys=DEEZER_COVER_IMAGE_KEYS)
            if image_url:
                return image_url

        return _extract_image_url(track_node, keys=DEEZER_COVER_IMAGE_KEYS)

    async def get_album_image(self, *, artist_name: str, album_name: str) -> str | None:
        query = _build_query(artist=artist_name, album=album_name)
        if not query:
            return None

        payload = await self._request("search/album", params={"q": query, "limit": 1})
        album_node = self._first_data_node(payload)
        if album_node:
            image_url = _extract_image_url(album_node, keys=DEEZER_COVER_IMAGE_KEYS)
            if image_url:
                return image_url

        fallback_payload = await self._request("search", params={"q": query, "limit": 1})
        track_node = self._first_data_node(fallback_payload)
        if not track_node:
            return None

        fallback_album_node = _as_dict(track_node.get("album"))
        if not fallback_album_node:
            return None

        return _extract_image_url(fallback_album_node, keys=DEEZER_COVER_IMAGE_KEYS)
