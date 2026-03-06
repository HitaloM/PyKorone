from __future__ import annotations

import asyncio
import html
import re
import unicodedata

import aiohttp
import orjson

from korone.utils.aiohttp_session import HTTPClient


class DeezerError(Exception):
    pass


class DeezerClient:
    __slots__ = ("base_url", "timeout")

    BASE_URL = "https://api.deezer.com"
    TIMEOUT_SECONDS = 12
    SEARCH_LIMIT = 5
    SEARCH_STRICT_MODE = "on"
    RETRY_ATTEMPTS = 2
    RETRYABLE_STATUSES = frozenset({429, 500, 502, 503, 504})
    RETRY_BACKOFF_SECONDS = (0.4, 1.0)
    ARTIST_IMAGE_KEYS = ("picture_xl", "picture_big", "picture_medium", "picture_small", "picture")
    COVER_IMAGE_KEYS = ("cover_xl", "cover_big", "cover_medium", "cover_small", "cover")
    COMPARISON_SANITIZER_RE = re.compile(r"[\W_]+")

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or self.BASE_URL).rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=self.TIMEOUT_SECONDS)

    @staticmethod
    def _as_dict(value: object) -> dict[str, object] | None:
        return value if isinstance(value, dict) else None

    @staticmethod
    def _text(value: object) -> str | None:
        if isinstance(value, str) and value.strip():
            return html.unescape(value).strip()
        return None

    @classmethod
    def _data_nodes(cls, payload: dict[str, object]) -> list[dict[str, object]]:
        data = payload.get("data")
        if not isinstance(data, list):
            return []
        return [node for node in data if isinstance(node, dict)]

    @classmethod
    def _title(cls, node: dict[str, object]) -> str | None:
        return cls._text(node.get("title")) or cls._text(node.get("title_short"))

    @classmethod
    def _image_url(cls, node: dict[str, object], *, keys: tuple[str, ...]) -> str | None:
        for key in keys:
            if image_url := cls._text(node.get(key)):
                return image_url
        return None

    @classmethod
    def _track_image_url(cls, track_node: dict[str, object]) -> str | None:
        if image_url := cls._image_url(track_node, keys=cls.COVER_IMAGE_KEYS):
            return image_url

        if album_node := cls._as_dict(track_node.get("album")):
            return cls._image_url(album_node, keys=cls.COVER_IMAGE_KEYS)

        return None

    @staticmethod
    def _normalize_query_value(value: str) -> str:
        return " ".join(value.replace('"', " ").split())

    @classmethod
    def _normalize_name(cls, value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value)
        without_marks = "".join(char for char in normalized if not unicodedata.combining(char))
        sanitized = cls.COMPARISON_SANITIZER_RE.sub(" ", without_marks.casefold())
        return " ".join(sanitized.split())

    @classmethod
    def _same_name(cls, expected: str, actual: object) -> bool:
        if not (actual_value := cls._text(actual)):
            return False
        return cls._normalize_name(expected) == cls._normalize_name(actual_value)

    @classmethod
    def _build_query(cls, *, artist: str | None = None, track: str | None = None, album: str | None = None) -> str:
        return " ".join(
            f'{field}:"{normalized}"'
            for field, value in (("artist", artist), ("track", track), ("album", album))
            if value and (normalized := cls._normalize_query_value(value))
        )

    @classmethod
    def _build_track_queries(cls, *, artist_name: str, track_name: str, album_name: str | None) -> tuple[str, ...]:
        queries = [
            query
            for query in (
                cls._build_query(artist=artist_name, track=track_name, album=album_name) if album_name else "",
                cls._build_query(artist=artist_name, track=track_name),
            )
            if query
        ]
        return tuple(dict.fromkeys(queries))

    @classmethod
    def _search_params(cls, query: str) -> dict[str, str | int]:
        return {"q": query, "limit": cls.SEARCH_LIMIT, "strict": cls.SEARCH_STRICT_MODE}

    @classmethod
    def _album_matches(cls, album_node: dict[str, object], *, artist_name: str, album_name: str) -> bool:
        if not cls._same_name(album_name, cls._title(album_node)):
            return False

        artist_node = cls._as_dict(album_node.get("artist"))
        if not artist_node:
            return False

        return cls._same_name(artist_name, artist_node.get("name"))

    @classmethod
    def _track_matches(
        cls, track_node: dict[str, object], *, artist_name: str, track_name: str, album_name: str | None
    ) -> bool:
        if not cls._same_name(track_name, cls._title(track_node)):
            return False

        artist_node = cls._as_dict(track_node.get("artist"))
        if not artist_node or not cls._same_name(artist_name, artist_node.get("name")):
            return False

        if album_name is None:
            return True

        album_node = cls._as_dict(track_node.get("album"))
        return bool(album_node) and cls._same_name(album_name, cls._title(album_node))

    @classmethod
    async def _retry_delay(cls, attempt: int) -> None:
        index = min(attempt, len(cls.RETRY_BACKOFF_SECONDS) - 1)
        await asyncio.sleep(cls.RETRY_BACKOFF_SECONDS[index])

    async def _request(self, path: str, *, params: dict[str, str | int]) -> dict[str, object]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        session = await HTTPClient.get_session()
        max_attempt_index = self.RETRY_ATTEMPTS

        for attempt in range(max_attempt_index + 1):
            try:
                async with session.get(url, params=params, timeout=self.timeout) as response:
                    if response.status != 200:
                        if response.status in self.RETRYABLE_STATUSES and attempt < max_attempt_index:
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

    async def _search_nodes(self, path: str, query: str) -> list[dict[str, object]]:
        payload = await self._request(path, params=self._search_params(query))
        return self._data_nodes(payload)

    async def get_artist_image(self, artist_name: str) -> str | None:
        for artist_node in await self._search_nodes("search/artist", artist_name):
            if not self._same_name(artist_name, artist_node.get("name")):
                continue

            image_url = self._image_url(artist_node, keys=self.ARTIST_IMAGE_KEYS)
            if image_url:
                return image_url

        return None

    async def get_track_image(self, *, artist_name: str, track_name: str, album_name: str | None = None) -> str | None:
        for query in self._build_track_queries(artist_name=artist_name, track_name=track_name, album_name=album_name):
            for track_node in await self._search_nodes("search/track", query):
                if not self._track_matches(
                    track_node, artist_name=artist_name, track_name=track_name, album_name=album_name
                ):
                    continue

                image_url = self._track_image_url(track_node)
                if image_url:
                    return image_url

        if album_name:
            return await self.get_album_image(artist_name=artist_name, album_name=album_name)

        return None

    async def get_album_image(self, *, artist_name: str, album_name: str) -> str | None:
        query = self._build_query(artist=artist_name, album=album_name)
        if not query:
            return None

        for album_node in await self._search_nodes("search/album", query):
            if not self._album_matches(album_node, artist_name=artist_name, album_name=album_name):
                continue

            image_url = self._image_url(album_node, keys=self.COVER_IMAGE_KEYS)
            if image_url:
                return image_url

        return None
