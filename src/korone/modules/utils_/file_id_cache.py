from __future__ import annotations

import hashlib
from typing import Any

import orjson

from korone import aredis
from korone.constants import CACHE_FILE_ID_TTL_SECONDS

_CACHE_PREFIX = "telegram:file-id"


def make_file_id_cache_key(namespace: str, identifier: str) -> str:
    digest = hashlib.sha256(identifier.encode("utf-8")).hexdigest()
    return f"{_CACHE_PREFIX}:{namespace}:{digest}"


async def get_cached_file_payload(cache_key: str) -> dict[str, Any] | None:
    raw = await aredis.get(cache_key)
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
    cache_key: str, payload: dict[str, Any], *, ttl: int = CACHE_FILE_ID_TTL_SECONDS
) -> None:
    await aredis.set(cache_key, orjson.dumps(payload), ex=ttl)


async def delete_cached_file_payload(cache_key: str) -> None:
    await aredis.delete(cache_key)
