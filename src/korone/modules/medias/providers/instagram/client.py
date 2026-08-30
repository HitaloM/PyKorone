import asyncio
from typing import TYPE_CHECKING

import aiohttp

from korone.logger import get_logger
from korone.modules.medias.download import DEFAULT_MEDIA_HEADERS, DEFAULT_MEDIA_TIMEOUT
from korone.modules.medias.models import MediaKind

from . import parser
from .models import InstaData, InstaMedia

if TYPE_CHECKING:
    from korone.http import HttpClient

logger = get_logger(__name__)


class InstagramClient:
    __slots__ = ("_http",)

    _HEADERS = DEFAULT_MEDIA_HEADERS | {"User-Agent": "TelegramBot (like TwitterBot)"}
    _PROBE_TIMEOUT = aiohttp.ClientTimeout(total=15)
    _MAX_MEDIA_ITEMS = 10

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    async def get_data(self, instafix_url: str) -> InstaData | None:
        try:
            async with self._http.session.get(
                instafix_url, timeout=DEFAULT_MEDIA_TIMEOUT, headers=self._HEADERS, allow_redirects=True
            ) as response:
                if response.status != 200:
                    await logger.adebug("[Instagram] Non-200 response", status=response.status, url=instafix_url)
                    return None
                scraped = parser.scrape_instafix_data(await response.text())
                if not scraped:
                    return None
                media = await self._discover_media(instafix_url)
                return (
                    InstaData(media=media, username=scraped.username, description=scraped.description)
                    if media
                    else scraped
                )
        except (aiohttp.ClientError, aiohttp.ContentTypeError) as error:
            await logger.awarning("[Instagram] Fetch failed", error=str(error), url=instafix_url)
            return None

    async def _discover_media(self, instafix_url: str) -> tuple[InstaMedia, ...]:
        post_id = parser.extract_post_id(instafix_url)
        if not post_id:
            return ()

        results: list[InstaMedia | None] = [None] * self._MAX_MEDIA_ITEMS
        async with asyncio.TaskGroup() as task_group:
            for media_index in (1, 2):
                task_group.create_task(self._probe(instafix_url, post_id, media_index, results))
        if results[0] is None:
            return ()
        if results[1] is None:
            return (results[0],)

        async with asyncio.TaskGroup() as task_group:
            for media_index in range(3, self._MAX_MEDIA_ITEMS + 1):
                task_group.create_task(self._probe(instafix_url, post_id, media_index, results))
        media: list[InstaMedia] = []
        for item in results:
            if item is None:
                break
            media.append(item)
        return tuple(media)

    async def _probe(self, instafix_url: str, post_id: str, media_index: int, results: list[InstaMedia | None]) -> None:
        media_url = parser.build_offload_url(instafix_url, post_id, media_index)
        try:
            async with self._http.session.head(
                media_url, timeout=self._PROBE_TIMEOUT, headers=DEFAULT_MEDIA_HEADERS, allow_redirects=True
            ) as response:
                if media := self._media_from_probe(media_url, response):
                    results[media_index - 1] = media
        except TimeoutError, aiohttp.ClientError:
            return

    @staticmethod
    def _media_from_probe(media_url: str, response: aiohttp.ClientResponse) -> InstaMedia | None:
        if response.status not in {200, 206}:
            return None
        content_type = response.headers.get("Content-Type", "").partition(";")[0].strip().casefold()
        if content_type.startswith("video/"):
            return InstaMedia(url=media_url, kind=MediaKind.VIDEO, thumbnail_url=f"{media_url}?thumbnail=1")
        if content_type.startswith("image/"):
            return InstaMedia(url=media_url, kind=MediaKind.PHOTO)
        return None
