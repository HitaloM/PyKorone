# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

import asyncio
from collections.abc import Callable
from typing import Any

import orjson
from aiohttp import ClientResponse, ClientSession, TCPConnector

HEADERS: dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0"
}


class AiohttpSession:
    def __init__(self):
        self._session: ClientSession | None = None
        self.json_dumps: Callable[..., str] = lambda obj: orjson.dumps(obj).decode()

    async def _get_session(self) -> ClientSession:
        if self._session is None:
            connector = TCPConnector()
            self._session = ClientSession(
                connector=connector, headers=HEADERS, json_serialize=self.json_dumps
            )

        return self._session

    async def get(
        self, url: str, *, allow_redirects: bool = True, **kwargs: Any
    ) -> ClientResponse:
        session = await self._get_session()
        return await session.get(url, allow_redirects=allow_redirects, **kwargs)

    async def close(self) -> None:
        if not self._session:
            return

        if self._session.closed:
            return

        await self._session.close()

        # Wait 250 ms for the underlying SSL connections to close
        # https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
        await asyncio.sleep(0.250)


http_session = AiohttpSession()
