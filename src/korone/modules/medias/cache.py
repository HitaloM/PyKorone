import hashlib
from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationError
from redis.exceptions import RedisError

from korone.constants import CACHE_FILE_ID_TTL_SECONDS
from korone.logger import get_logger

from .models import DeliveredMedia, DeliveryReceipt, MediaKind, MediaPost, PreparedMedia, ProviderInfo
from .urls import normalize_media_url

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from redis.asyncio import Redis

type _NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

_CACHE_PREFIX = "media:v2"
logger = get_logger(__name__)


class _CachedMedia(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    kind: MediaKind
    file_id: _NonEmptyText
    source_url: _NonEmptyText
    duration: int | None = None
    width: int | None = None
    height: int | None = None

    @classmethod
    def from_delivery(cls, delivered: DeliveredMedia) -> _CachedMedia:
        media = delivered.media
        return cls(
            kind=media.kind,
            file_id=delivered.file_id,
            source_url=media.source_url,
            duration=media.duration,
            width=media.width,
            height=media.height,
        )

    def to_prepared(self, index: int) -> PreparedMedia:
        return PreparedMedia(
            kind=self.kind,
            file=self.file_id,
            filename=f"cached_media_{index}",
            source_url=self.source_url,
            duration=self.duration,
            width=self.width,
            height=self.height,
        )


class _CachedPost(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    author_name: str = ""
    author_handle: str = ""
    text: str = ""
    url: _NonEmptyText
    website: _NonEmptyText
    media: tuple[_CachedMedia, ...] = Field(min_length=1)
    quote_text: str | None = None
    quote_author_name: str | None = None
    quote_author_handle: str | None = None

    @classmethod
    def from_delivery(cls, post: MediaPost, receipt: DeliveryReceipt) -> _CachedPost:
        return cls(
            author_name=post.author_name,
            author_handle=post.author_handle,
            text=post.text,
            url=post.url,
            website=post.website,
            media=tuple(_CachedMedia.from_delivery(delivered) for delivered in receipt.media),
            quote_text=post.quote_text,
            quote_author_name=post.quote_author_name,
            quote_author_handle=post.quote_author_handle,
        )

    def to_post(self, provider: ProviderInfo) -> MediaPost:
        author_handle = self.author_handle or provider.name.casefold()
        return MediaPost(
            author_name=self.author_name or provider.name,
            author_handle=author_handle,
            text=self.text,
            url=self.url,
            website=self.website,
            media=tuple(media.to_prepared(index) for index, media in enumerate(self.media, start=1)),
            quote_text=self.quote_text or None,
            quote_author_name=self.quote_author_name or None,
            quote_author_handle=self.quote_author_handle or None,
        )


class _SourceFile(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    file_id: _NonEmptyText


class MediaCache:
    __slots__ = ("_redis", "_ttl")

    def __init__(self, redis: Redis, *, ttl: int = CACHE_FILE_ID_TTL_SECONDS) -> None:
        self._redis = redis
        self._ttl = ttl

    async def get_post(self, provider: ProviderInfo, source_url: str) -> tuple[str, MediaPost] | None:
        for candidate_url in self._post_candidates(source_url):
            key = self._key("post", candidate_url)
            raw = await self._get(key)
            if raw is None:
                continue
            try:
                cached = _CachedPost.model_validate_json(raw)
            except ValidationError:
                await self._delete_many((key,))
                continue
            return candidate_url, cached.to_post(provider)
        return None

    async def set_post(self, source_url: str, post: MediaPost, receipt: DeliveryReceipt) -> None:
        if not receipt.media:
            return
        payload = _CachedPost.from_delivery(post, receipt).model_dump_json()
        values = {self._key("post", url): payload for url in self._post_candidates(source_url, post.url)}
        await self._set_many(values)

    async def delete_post_and_sources(self, post: MediaPost, *urls: str) -> None:
        keys = [self._key("post", url) for url in self._post_candidates(*urls)]
        keys.extend(self._key("source", media.source_url) for media in post.media if media.source_url)
        await self._delete_many(keys)

    async def get_source_file_ids(self, source_urls: Sequence[str]) -> list[str | None]:
        keys = tuple(self._key("source", url) for url in source_urls)
        raw_payloads = await self._get_many(keys)
        resolved: list[str | None] = []
        invalid_keys: list[str] = []
        for key, raw in zip(keys, raw_payloads, strict=True):
            if raw is None:
                resolved.append(None)
                continue
            try:
                resolved.append(_SourceFile.model_validate_json(raw).file_id)
            except ValidationError:
                invalid_keys.append(key)
                resolved.append(None)
        await self._delete_many(invalid_keys)
        return resolved

    async def set_source_file_ids(self, entries: Sequence[tuple[str, str]]) -> None:
        values = {
            self._key("source", source_url): _SourceFile(file_id=file_id).model_dump_json()
            for source_url, file_id in entries
        }
        await self._set_many(values)

    async def _get(self, key: str) -> bytes | str | None:
        try:
            return await self._redis.get(key)
        except (RedisError, RuntimeError) as error:
            await logger.awarning("[MediaCache] Could not read payload", cache_key=key, error=str(error))
            return None

    async def _get_many(self, keys: Sequence[str]) -> list[bytes | str | None]:
        if not keys:
            return []
        try:
            return await self._redis.mget(keys)
        except (RedisError, RuntimeError) as error:
            await logger.awarning("[MediaCache] Could not read payloads", cache_key_count=len(keys), error=str(error))
            return [None] * len(keys)

    async def _set_many(self, values: Mapping[str, str]) -> None:
        if not values:
            return
        try:
            async with self._redis.pipeline(transaction=False) as pipeline:
                for key, payload in values.items():
                    pipeline.set(key, payload, ex=self._ttl)
                await pipeline.execute()
        except (RedisError, RuntimeError) as error:
            await logger.awarning(
                "[MediaCache] Could not persist payloads", cache_key_count=len(values), error=str(error)
            )

    async def _delete_many(self, keys: Iterable[str]) -> None:
        unique_keys = tuple(dict.fromkeys(keys))
        if not unique_keys:
            return
        try:
            await self._redis.delete(*unique_keys)
        except (RedisError, RuntimeError) as error:
            await logger.awarning(
                "[MediaCache] Could not delete payloads", cache_key_count=len(unique_keys), error=str(error)
            )

    @staticmethod
    def _key(kind: str, identifier: str) -> str:
        normalized = normalize_media_url(identifier) or identifier.strip() or identifier
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return f"{_CACHE_PREFIX}:{kind}:{digest}"

    @staticmethod
    def _post_candidates(*urls: str) -> tuple[str, ...]:
        return tuple(dict.fromkeys(url.strip() for url in urls if url.strip()))
