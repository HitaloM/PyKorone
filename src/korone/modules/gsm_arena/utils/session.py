from __future__ import annotations

import secrets
from typing import TYPE_CHECKING

import orjson

from korone import aredis

from .types import PhoneSearchResult

if TYPE_CHECKING:
    from collections.abc import Sequence

SESSION_TTL_SECONDS = 60 * 60
SESSION_KEY_PREFIX = "gsmarena:session:"


def _session_key(token: str) -> str:
    return f"{SESSION_KEY_PREFIX}{token}"


async def create_search_session(devices: Sequence[PhoneSearchResult]) -> str:
    token = secrets.token_hex(6)
    payload = [{"n": device.name, "u": device.url} for device in devices]
    await aredis.set(_session_key(token), orjson.dumps(payload), ex=SESSION_TTL_SECONDS)
    return token


async def get_search_session(token: str) -> list[PhoneSearchResult] | None:
    raw_payload = await aredis.get(_session_key(token))
    if raw_payload is None:
        return None

    try:
        parsed_payload = orjson.loads(raw_payload)
    except orjson.JSONDecodeError:
        return None

    if not isinstance(parsed_payload, list):
        return None

    devices: list[PhoneSearchResult] = []
    for item in parsed_payload:
        if not isinstance(item, dict):
            return None

        name = item.get("n")
        url = item.get("u")
        if not isinstance(name, str) or not isinstance(url, str):
            return None

        devices.append(PhoneSearchResult(name=name, url=url))

    return devices
