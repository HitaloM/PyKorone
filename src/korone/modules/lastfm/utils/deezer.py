import asyncio
import re
import unicodedata

import aiohttp
import orjson
from pydantic import BaseModel, TypeAdapter, ValidationError

from korone.utils.aiohttp_session import HTTPClient

from ._schemas import (
    _DeezerAlbumPayload,
    _DeezerAlbumSearchPayload,
    _DeezerArtistPayload,
    _DeezerArtistSearchPayload,
    _DeezerCoverPayload,
    _DeezerTrackPayload,
    _DeezerTrackSearchPayload,
)

_ROOT_PAYLOAD_ADAPTER = TypeAdapter(dict[str, object])


class DeezerError(Exception):
    pass


def _validate_payload[T: BaseModel](model_type: type[T], payload: object) -> T:
    try:
        return model_type.model_validate(payload)
    except ValidationError as exc:
        msg = "Deezer returned an unexpected payload format."
        raise DeezerError(msg) from exc


class DeezerClient:
    __slots__ = ("base_url", "timeout")

    BASE_URL = "https://api.deezer.com"
    TIMEOUT_SECONDS = 12
    SEARCH_LIMIT = 5
    SEARCH_STRICT_MODE = "on"
    RETRY_ATTEMPTS = 2
    RETRYABLE_STATUSES = frozenset({429, 500, 502, 503, 504})
    RETRY_BACKOFF_SECONDS = (0.4, 1.0)
    COMPARISON_SANITIZER_RE = re.compile(r"[\W_]+")

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or self.BASE_URL).rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=self.TIMEOUT_SECONDS)

    @staticmethod
    def _title(node: _DeezerAlbumPayload | _DeezerTrackPayload) -> str | None:
        return node.title or node.title_short

    @staticmethod
    def _artist_image_url(node: _DeezerArtistPayload) -> str | None:
        return node.picture_xl or node.picture_big or node.picture_medium or node.picture_small or node.picture

    @staticmethod
    def _cover_image_url(node: _DeezerCoverPayload) -> str | None:
        return node.cover_xl or node.cover_big or node.cover_medium or node.cover_small or node.cover

    @classmethod
    def _track_image_url(cls, track: _DeezerTrackPayload) -> str | None:
        return cls._cover_image_url(track) or (cls._cover_image_url(track.album) if track.album else None)

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
    def _same_name(cls, expected: str, actual: str | None) -> bool:
        if not actual:
            return False
        return cls._normalize_name(expected) == cls._normalize_name(actual)

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
    def _album_matches(cls, album: _DeezerAlbumPayload, *, artist_name: str, album_name: str) -> bool:
        if not cls._same_name(album_name, cls._title(album)):
            return False

        return album.artist is not None and cls._same_name(artist_name, album.artist.name)

    @classmethod
    def _track_matches(
        cls, track: _DeezerTrackPayload, *, artist_name: str, track_name: str, album_name: str | None
    ) -> bool:
        if not cls._same_name(track_name, cls._title(track)):
            return False

        if track.artist is None or not cls._same_name(artist_name, track.artist.name):
            return False

        if album_name is None:
            return True

        return track.album is not None and cls._same_name(album_name, cls._title(track.album))

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
                        raw_payload: object = await response.json(content_type=None, loads=orjson.loads)
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

            try:
                payload = _ROOT_PAYLOAD_ADAPTER.validate_python(raw_payload)
            except ValidationError as exc:
                msg = "Deezer returned an unexpected payload format."
                raise DeezerError(msg) from exc

            return payload

        msg = "Deezer request failed."
        raise DeezerError(msg)

    async def _search_artists(self, query: str) -> list[_DeezerArtistPayload]:
        payload = await self._request("search/artist", params=self._search_params(query))
        return _validate_payload(_DeezerArtistSearchPayload, payload).data

    async def _search_tracks(self, query: str) -> list[_DeezerTrackPayload]:
        payload = await self._request("search/track", params=self._search_params(query))
        return _validate_payload(_DeezerTrackSearchPayload, payload).data

    async def _search_albums(self, query: str) -> list[_DeezerAlbumPayload]:
        payload = await self._request("search/album", params=self._search_params(query))
        return _validate_payload(_DeezerAlbumSearchPayload, payload).data

    async def get_artist_image(self, artist_name: str) -> str | None:
        for artist in await self._search_artists(artist_name):
            if not self._same_name(artist_name, artist.name):
                continue

            image_url = self._artist_image_url(artist)
            if image_url:
                return image_url

        return None

    async def get_track_image(self, *, artist_name: str, track_name: str, album_name: str | None = None) -> str | None:
        for query in self._build_track_queries(artist_name=artist_name, track_name=track_name, album_name=album_name):
            for track in await self._search_tracks(query):
                if not self._track_matches(
                    track, artist_name=artist_name, track_name=track_name, album_name=album_name
                ):
                    continue

                image_url = self._track_image_url(track)
                if image_url:
                    return image_url

        if album_name:
            return await self.get_album_image(artist_name=artist_name, album_name=album_name)

        return None

    async def get_album_image(self, *, artist_name: str, album_name: str) -> str | None:
        query = self._build_query(artist=artist_name, album=album_name)
        if not query:
            return None

        for album in await self._search_albums(query):
            if not self._album_matches(album, artist_name=artist_name, album_name=album_name):
                continue

            image_url = self._cover_image_url(album)
            if image_url:
                return image_url

        return None
