import hashlib
from typing import TYPE_CHECKING, Any

import orjson
from redis.exceptions import RedisError

from korone import aredis
from korone.constants import CACHE_FILE_ID_TTL_SECONDS
from korone.logger import get_logger

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

_CACHE_PREFIX = "telegram:file-id"
logger = get_logger(__name__)


def make_file_id_cache_key(namespace: str, identifier: str) -> str:
    digest = hashlib.sha256(identifier.encode("utf-8")).hexdigest()
    return f"{_CACHE_PREFIX}:{namespace}:{digest}"


def _deserialize_payload(raw: bytes | str | None) -> dict[str, Any] | None:
    if not raw:
        return None

    try:
        payload = orjson.loads(raw)
    except orjson.JSONDecodeError:
        return None

    return payload if isinstance(payload, dict) else None


async def get_cached_file_payload(cache_key: str) -> dict[str, Any] | None:
    try:
        raw = await aredis.get(cache_key)
    except (RedisError, RuntimeError) as exc:
        await logger.awarning("[FileIdCache] Could not read cache payload", cache_key=cache_key, error=str(exc))
        return None

    return _deserialize_payload(raw)


async def get_cached_file_payloads(cache_keys: Sequence[str]) -> list[dict[str, Any] | None]:
    keys = tuple(cache_keys)
    if not keys:
        return []

    try:
        raw_payloads = await aredis.mget(keys)
    except (RedisError, RuntimeError) as exc:
        await logger.awarning("[FileIdCache] Could not read cache payloads", cache_key_count=len(keys), error=str(exc))
        return [None] * len(keys)

    return [_deserialize_payload(raw) for raw in raw_payloads]


async def set_cached_file_payload(
    cache_key: str, payload: Mapping[str, Any], *, ttl: int = CACHE_FILE_ID_TTL_SECONDS
) -> None:
    try:
        await aredis.set(cache_key, orjson.dumps(payload), ex=ttl)
    except (RedisError, RuntimeError) as exc:
        await logger.awarning("[FileIdCache] Could not persist cache payload", cache_key=cache_key, error=str(exc))


async def set_cached_file_payloads(
    payloads: Mapping[str, Mapping[str, Any]], *, ttl: int = CACHE_FILE_ID_TTL_SECONDS
) -> None:
    if not payloads:
        return

    try:
        async with aredis.pipeline(transaction=False) as pipeline:
            for cache_key, payload in payloads.items():
                pipeline.set(cache_key, orjson.dumps(payload), ex=ttl)
            await pipeline.execute()
    except (RedisError, RuntimeError) as exc:
        await logger.awarning(
            "[FileIdCache] Could not persist cache payloads", cache_key_count=len(payloads), error=str(exc)
        )


async def delete_cached_file_payload(cache_key: str) -> None:
    try:
        await aredis.delete(cache_key)
    except (RedisError, RuntimeError) as exc:
        await logger.awarning("[FileIdCache] Could not delete cache payload", cache_key=cache_key, error=str(exc))


async def delete_cached_file_payloads(cache_keys: Iterable[str]) -> None:
    keys = tuple(dict.fromkeys(cache_keys))
    if not keys:
        return

    try:
        await aredis.delete(*keys)
    except (RedisError, RuntimeError) as exc:
        await logger.awarning(
            "[FileIdCache] Could not delete cache payloads", cache_key_count=len(keys), error=str(exc)
        )
