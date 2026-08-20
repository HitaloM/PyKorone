import secrets
from typing import TYPE_CHECKING

import orjson
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

from korone import aredis

from .types import PhoneSearchResult

if TYPE_CHECKING:
    from collections.abc import Sequence

SESSION_TTL_SECONDS = 60 * 60
SESSION_KEY_PREFIX = "gsmarena:session:"


class _SearchSessionEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = Field(alias="n", strict=True)
    url: str = Field(alias="u", strict=True)


_SESSION_ADAPTER = TypeAdapter(list[_SearchSessionEntry])


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
        parsed_payload = _SESSION_ADAPTER.validate_json(raw_payload)
    except ValidationError:
        return None

    return [PhoneSearchResult(name=item.name, url=item.url) for item in parsed_payload]
