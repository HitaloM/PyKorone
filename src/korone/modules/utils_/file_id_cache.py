from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Any

import orjson
from redis.exceptions import RedisError

from korone import aredis
from korone.constants import CACHE_FILE_ID_TTL_SECONDS
from korone.logger import get_logger

if TYPE_CHECKING:
    from collections.abc import Mapping

_CACHE_PREFIX = "telegram:file-id"
logger = get_logger(__name__)


def make_file_id_cache_key(namespace: str, identifier: str) -> str:
    digest = hashlib.sha256(identifier.encode("utf-8")).hexdigest()
    return f"{_CACHE_PREFIX}:{namespace}:{digest}"


async def get_cached_file_payload(cache_key: str) -> dict[str, Any] | None:
    try:
        raw = await aredis.get(cache_key)
    except (RedisError, RuntimeError) as exc:
        await logger.awarning("[FileIdCache] Could not read cache payload", cache_key=cache_key, error=str(exc))
        return None

    if not raw:
        return None

    try:
        payload = orjson.loads(raw)
    except orjson.JSONDecodeError:
        return None

    if not isinstance(payload, dict):
        return None

    return payload


async def set_cached_file_payload(
    cache_key: str, payload: Mapping[str, Any], *, ttl: int = CACHE_FILE_ID_TTL_SECONDS
) -> None:
    try:
        await aredis.set(cache_key, orjson.dumps(payload), ex=ttl)
    except (RedisError, RuntimeError) as exc:
        await logger.awarning("[FileIdCache] Could not persist cache payload", cache_key=cache_key, error=str(exc))


async def delete_cached_file_payload(cache_key: str) -> None:
    try:
        await aredis.delete(cache_key)
    except (RedisError, RuntimeError) as exc:
        await logger.awarning("[FileIdCache] Could not delete cache payload", cache_key=cache_key, error=str(exc))
