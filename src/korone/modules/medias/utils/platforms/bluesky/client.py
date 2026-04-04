from __future__ import annotations

from typing import Any

import aiohttp
import orjson

from korone.logger import get_logger
from korone.modules.medias.utils.parsing import coerce_str, dict_list, dict_or_empty
from korone.utils.aiohttp_session import HTTPClient

from .constants import BSKY_PLC_DIRECTORY, BSKY_POST_THREAD, BSKY_RESOLVE_HANDLE, HTTP_TIMEOUT

logger = get_logger(__name__)
_REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=HTTP_TIMEOUT)


async def resolve_handle(handle: str) -> str | None:
    params = {"handle": handle}
    try:
        session = await HTTPClient.get_session()
        async with session.get(BSKY_RESOLVE_HANDLE, timeout=_REQUEST_TIMEOUT, params=params) as response:
            if response.status != 200:
                await logger.adebug("[Bluesky] Resolve handle failed", status=response.status, handle=handle)
                return None

            data = await response.json(loads=orjson.loads)
            return coerce_str(dict_or_empty(data).get("did"))
    except (aiohttp.ClientError, aiohttp.ContentTypeError) as exc:
        await logger.aerror("[Bluesky] Resolve handle error", error=str(exc))
        return None


async def resolve_pds_url(did: str) -> str | None:
    if did.startswith("did:plc:"):
        url = f"{BSKY_PLC_DIRECTORY}/{did}"
    elif did.startswith("did:web:"):
        domain = did.removeprefix("did:web:")
        url = f"https://{domain}/.well-known/did.json"
    else:
        return None

    try:
        session = await HTTPClient.get_session()
        async with session.get(url, timeout=_REQUEST_TIMEOUT) as response:
            if response.status != 200:
                await logger.adebug("[Bluesky] PLC directory lookup failed", status=response.status, did=did)
                return None

            data = dict_or_empty(await response.json(loads=orjson.loads))
            for service in dict_list(data.get("service")):
                if coerce_str(service.get("id")) == "#atproto_pds":
                    return coerce_str(service.get("serviceEndpoint"))
            return None
    except (aiohttp.ClientError, aiohttp.ContentTypeError) as exc:
        await logger.aerror("[Bluesky] PDS resolution error", error=str(exc))
        return None


async def get_post_thread(uri: str) -> dict[str, Any] | None:
    params = {"uri": uri, "depth": 0}
    try:
        session = await HTTPClient.get_session()
        async with session.get(BSKY_POST_THREAD, timeout=_REQUEST_TIMEOUT, params=params) as response:
            if response.status != 200:
                await logger.adebug("[Bluesky] Post thread failed", status=response.status, uri=uri)
                return None

            data = await response.json(loads=orjson.loads)
            thread = dict_or_empty(data)
            return thread or None
    except (aiohttp.ClientError, aiohttp.ContentTypeError) as exc:
        await logger.aerror("[Bluesky] Post thread error", error=str(exc))
        return None
