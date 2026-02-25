from __future__ import annotations

from typing import Any, cast

import aiohttp
import orjson

from korone.logger import get_logger
from korone.utils.aiohttp_session import HTTPClient

from .constants import BSKY_PLC_DIRECTORY, BSKY_POST_THREAD, BSKY_RESOLVE_HANDLE, HTTP_TIMEOUT

logger = get_logger(__name__)


async def resolve_handle(handle: str) -> str | None:
    timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT)
    params = {"handle": handle}
    try:
        session = await HTTPClient.get_session()
        async with session.get(BSKY_RESOLVE_HANDLE, timeout=timeout, params=params) as response:
            if response.status != 200:
                await logger.adebug("[Bluesky] Resolve handle failed", status=response.status, handle=handle)
                return None

            data = await response.json(loads=orjson.loads)
            return str(data.get("did")) if isinstance(data, dict) else None
    except (aiohttp.ClientError, aiohttp.ContentTypeError) as exc:
        await logger.aerror("[Bluesky] Resolve handle error", error=str(exc))
        return None


async def resolve_pds_url(did: str) -> str | None:
    timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT)
    if did.startswith("did:plc:"):
        url = f"{BSKY_PLC_DIRECTORY}/{did}"
    elif did.startswith("did:web:"):
        domain = did.removeprefix("did:web:")
        url = f"https://{domain}/.well-known/did.json"
    else:
        return None

    try:
        session = await HTTPClient.get_session()
        async with session.get(url, timeout=timeout) as response:
            if response.status != 200:
                await logger.adebug("[Bluesky] PLC directory lookup failed", status=response.status, did=did)
                return None

            data = await response.json(loads=orjson.loads)
            if not isinstance(data, dict):
                return None

            services = data.get("service")
            if not isinstance(services, list):
                return None

            for service in services:
                if isinstance(service, dict) and service.get("id") == "#atproto_pds":
                    endpoint = service.get("serviceEndpoint")
                    return str(endpoint) if isinstance(endpoint, str) else None
            return None
    except (aiohttp.ClientError, aiohttp.ContentTypeError) as exc:
        await logger.aerror("[Bluesky] PDS resolution error", error=str(exc))
        return None


async def get_post_thread(uri: str) -> dict[str, Any] | None:
    timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT)
    params = {"uri": uri, "depth": 0}
    try:
        session = await HTTPClient.get_session()
        async with session.get(BSKY_POST_THREAD, timeout=timeout, params=params) as response:
            if response.status != 200:
                await logger.adebug("[Bluesky] Post thread failed", status=response.status, uri=uri)
                return None

            data = await response.json(loads=orjson.loads)
            return cast("dict[str, Any]", data)
    except (aiohttp.ClientError, aiohttp.ContentTypeError) as exc:
        await logger.aerror("[Bluesky] Post thread error", error=str(exc))
        return None
