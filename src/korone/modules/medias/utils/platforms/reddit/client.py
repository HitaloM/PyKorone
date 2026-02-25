from __future__ import annotations

from typing import TYPE_CHECKING

from korone.utils.aiohttp_session import HTTPClient

if TYPE_CHECKING:
    import aiohttp


async def request_redlib_page(
    url: str, *, headers: dict[str, str], cookies: dict[str, str], request_timeout: aiohttp.ClientTimeout
) -> dict[str, str] | None:
    session = await HTTPClient.get_session()
    async with session.get(
        url, headers=headers, cookies=cookies, allow_redirects=True, timeout=request_timeout
    ) as response:
        if response.status != 200:
            return None

        html_content = await response.text()
        return {"html": html_content, "base_url": str(response.url)}


async def fetch_text(url: str, *, headers: dict[str, str], cookies: dict[str, str]) -> str | None:
    session = await HTTPClient.get_session()
    async with session.get(url, headers=headers, cookies=cookies) as response:
        if response.status != 200:
            return None
        return await response.text()
