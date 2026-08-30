from typing import TYPE_CHECKING, Any

import aiohttp
import orjson

from korone.logger import get_logger
from korone.modules.medias.parsing import coerce_str, dict_list, dict_or_empty

from .constants import BSKY_PLC_DIRECTORY, BSKY_POST_THREAD, BSKY_RESOLVE_HANDLE, HTTP_TIMEOUT

if TYPE_CHECKING:
    from korone.http import HttpClient

logger = get_logger(__name__)


class BlueskyClient:
    __slots__ = ("_http", "_timeout")

    def __init__(self, http: HttpClient) -> None:
        self._http = http
        self._timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT)

    async def resolve_handle(self, handle: str) -> str | None:
        try:
            async with self._http.session.get(
                BSKY_RESOLVE_HANDLE, timeout=self._timeout, params={"handle": handle}
            ) as response:
                if response.status != 200:
                    await logger.adebug("[Bluesky] Resolve handle failed", status=response.status, handle=handle)
                    return None
                data = await response.json(loads=orjson.loads)
                return coerce_str(dict_or_empty(data).get("did"))
        except (aiohttp.ClientError, aiohttp.ContentTypeError) as error:
            await logger.awarning("[Bluesky] Resolve handle error", error=str(error))
            return None

    async def resolve_pds_url(self, did: str) -> str | None:
        if did.startswith("did:plc:"):
            url = f"{BSKY_PLC_DIRECTORY}/{did}"
        elif did.startswith("did:web:"):
            url = f"https://{did.removeprefix('did:web:')}/.well-known/did.json"
        else:
            return None

        try:
            async with self._http.session.get(url, timeout=self._timeout) as response:
                if response.status != 200:
                    await logger.adebug("[Bluesky] PLC directory lookup failed", status=response.status, did=did)
                    return None
                data = dict_or_empty(await response.json(loads=orjson.loads))
                for service in dict_list(data.get("service")):
                    if coerce_str(service.get("id")) == "#atproto_pds":
                        return coerce_str(service.get("serviceEndpoint"))
        except (aiohttp.ClientError, aiohttp.ContentTypeError) as error:
            await logger.awarning("[Bluesky] PDS resolution error", error=str(error))
        return None

    async def get_post_thread(self, uri: str) -> dict[str, Any] | None:
        try:
            async with self._http.session.get(
                BSKY_POST_THREAD, timeout=self._timeout, params={"uri": uri, "depth": 0}
            ) as response:
                if response.status != 200:
                    await logger.adebug("[Bluesky] Post thread failed", status=response.status, uri=uri)
                    return None
                thread = dict_or_empty(await response.json(loads=orjson.loads))
                return thread or None
        except (aiohttp.ClientError, aiohttp.ContentTypeError) as error:
            await logger.awarning("[Bluesky] Post thread error", error=str(error))
            return None
