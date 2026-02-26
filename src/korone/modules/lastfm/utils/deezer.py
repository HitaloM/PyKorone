from __future__ import annotations

import asyncio

import aiohttp
import orjson

from korone.utils.aiohttp_session import HTTPClient

DEEZER_BASE_URL = "https://api.deezer.com"
DEEZER_TIMEOUT_SECONDS = 12
DEEZER_SEARCH_LIMIT = 5
DEEZER_RETRY_ATTEMPTS = 2
DEEZER_RETRYABLE_STATUSES = frozenset({429, 500, 502, 503, 504})
DEEZER_RETRY_BACKOFF_SECONDS = (0.4, 1.0)
DEEZER_ARTIST_IMAGE_KEYS = ("picture_xl", "picture_big", "picture_medium", "picture_small", "picture")
DEEZER_COVER_IMAGE_KEYS = ("cover_xl", "cover_big", "cover_medium", "cover_small", "cover")


def _as_dict(value: object) -> dict[str, object] | None:
    return value if isinstance(value, dict) else None


def _as_non_empty_str(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _as_dict_nodes(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [node for node in value if isinstance(node, dict)]


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


def _extract_track_image(track_node: dict[str, object]) -> str | None:
    image_url = _extract_image_url(track_node, keys=DEEZER_COVER_IMAGE_KEYS)
    if image_url:
        return image_url

    album_node = _as_dict(track_node.get("album"))
    if not album_node:
        return None

    return _extract_image_url(album_node, keys=DEEZER_COVER_IMAGE_KEYS)


def _build_track_queries(*, artist_name: str, track_name: str, album_name: str | None) -> tuple[str, ...]:
    queries: list[str] = []

    if album_name:
        query_with_album = _build_query(artist=artist_name, track=track_name, album=album_name)
        if query_with_album:
            queries.append(query_with_album)

    query_without_album = _build_query(artist=artist_name, track=track_name)
    if query_without_album and query_without_album not in queries:
        queries.append(query_without_album)

    return tuple(queries)


class DeezerError(Exception):
    """Raised when Deezer requests fail."""


class DeezerClient:
    __slots__ = ("base_url", "timeout")

    def __init__(self, base_url: str = DEEZER_BASE_URL) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=DEEZER_TIMEOUT_SECONDS)

    @staticmethod
    async def _retry_delay(attempt: int) -> None:
        index = min(attempt, len(DEEZER_RETRY_BACKOFF_SECONDS) - 1)
        await asyncio.sleep(DEEZER_RETRY_BACKOFF_SECONDS[index])

    async def _request(self, path: str, *, params: dict[str, str | int]) -> dict[str, object]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        session = await HTTPClient.get_session()
        max_attempt_index = DEEZER_RETRY_ATTEMPTS

        for attempt in range(max_attempt_index + 1):
            try:
                async with session.get(url, params=params, timeout=self.timeout) as response:
                    if response.status != 200:
                        if response.status in DEEZER_RETRYABLE_STATUSES and attempt < max_attempt_index:
                            await self._retry_delay(attempt)
                            continue

                        msg = f"Deezer request failed with status {response.status}."
                        raise DeezerError(msg)

                    try:
                        payload = await response.json(content_type=None, loads=orjson.loads)
                    except (aiohttp.ContentTypeError, ValueError) as exc:
                        msg = "Deezer returned an invalid payload."
                        raise DeezerError(msg) from exc
            except TimeoutError as exc:
                if attempt < max_attempt_index:
                    await self._retry_delay(attempt)
                    continue

                msg = "Deezer request timed out."
                raise DeezerError(msg) from exc
            except aiohttp.ClientError as exc:
                if attempt < max_attempt_index:
                    await self._retry_delay(attempt)
                    continue

                msg = "Deezer request failed."
                raise DeezerError(msg) from exc

            if not isinstance(payload, dict):
                msg = "Deezer returned an unexpected payload format."
                raise DeezerError(msg)

            return payload

        msg = "Deezer request failed."
        raise DeezerError(msg)

    @staticmethod
    def _data_nodes(payload: dict[str, object]) -> list[dict[str, object]]:
        return _as_dict_nodes(payload.get("data"))

    async def get_artist_image(self, artist_name: str) -> str | None:
        payload = await self._request("search/artist", params={"q": artist_name, "limit": DEEZER_SEARCH_LIMIT})
        for artist_node in self._data_nodes(payload):
            image_url = _extract_image_url(artist_node, keys=DEEZER_ARTIST_IMAGE_KEYS)
            if image_url:
                return image_url

        return None

    async def get_track_image(self, *, artist_name: str, track_name: str, album_name: str | None = None) -> str | None:
        queries = _build_track_queries(artist_name=artist_name, track_name=track_name, album_name=album_name)
        for query in queries:
            payload = await self._request("search", params={"q": query, "limit": DEEZER_SEARCH_LIMIT})
            for track_node in self._data_nodes(payload):
                image_url = _extract_track_image(track_node)
                if image_url:
                    return image_url

        return None

    async def get_album_image(self, *, artist_name: str, album_name: str) -> str | None:
        query = _build_query(artist=artist_name, album=album_name)
        if not query:
            return None

        payload = await self._request("search/album", params={"q": query, "limit": DEEZER_SEARCH_LIMIT})
        for album_node in self._data_nodes(payload):
            image_url = _extract_image_url(album_node, keys=DEEZER_COVER_IMAGE_KEYS)
            if image_url:
                return image_url

        fallback_payload = await self._request("search", params={"q": query, "limit": DEEZER_SEARCH_LIMIT})
        for track_node in self._data_nodes(fallback_payload):
            fallback_album_node = _as_dict(track_node.get("album"))
            if fallback_album_node:
                image_url = _extract_image_url(fallback_album_node, keys=DEEZER_COVER_IMAGE_KEYS)
                if image_url:
                    return image_url

            image_url = _extract_image_url(track_node, keys=DEEZER_COVER_IMAGE_KEYS)
            if image_url:
                return image_url

        return None
