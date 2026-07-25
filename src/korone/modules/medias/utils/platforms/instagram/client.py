import asyncio

import aiohttp

from korone.logger import get_logger
from korone.modules.medias.utils.provider_base import MediaProvider
from korone.modules.medias.utils.types import MediaKind
from korone.utils.aiohttp_session import HTTPClient

from . import parser
from .types import InstaData, InstaMedia

logger = get_logger(__name__)

_INSTAFIX_HEADERS = MediaProvider._DEFAULT_HEADERS | {"User-Agent": "TelegramBot (like TwitterBot)"}
_MEDIA_PROBE_TIMEOUT = aiohttp.ClientTimeout(total=15)
_MAX_MEDIA_ITEMS = 10


async def get_instafix_data(instafix_url: str) -> InstaData | None:
    try:
        session = await HTTPClient.get_session()
        async with session.get(
            instafix_url,
            timeout=MediaProvider._DEFAULT_TIMEOUT,
            headers=_INSTAFIX_HEADERS,
            allow_redirects=True,
        ) as response:
            if response.status != 200:
                await logger.adebug("[Instagram] Non-200 response", status=response.status, url=instafix_url)
                return None

            text = await response.text()
            scraped = parser.scrape_instafix_data(text)
            if not scraped:
                return None

            media = await discover_instafix_media(instafix_url)
            if not media:
                return scraped

            return InstaData(media=media, username=scraped.username, description=scraped.description)
    except (aiohttp.ClientError, aiohttp.ContentTypeError) as exc:
        await logger.aerror("[Instagram] Fetch failed", error=str(exc), url=instafix_url)
        return None


async def discover_instafix_media(instafix_url: str) -> tuple[InstaMedia, ...]:
    post_id = parser.extract_post_id(instafix_url)
    if not post_id:
        return ()

    results: list[InstaMedia | None] = [None] * _MAX_MEDIA_ITEMS

    async with asyncio.TaskGroup() as task_group:
        for media_index in range(1, _MAX_MEDIA_ITEMS + 1):
            task_group.create_task(_probe_media(instafix_url, post_id, media_index, results))

    media: list[InstaMedia] = []
    for item in results:
        if item is None:
            break
        media.append(item)
    return tuple(media)


async def _probe_media(
    instafix_url: str,
    post_id: str,
    media_index: int,
    results: list[InstaMedia | None],
) -> None:
    media_url = parser.build_offload_url(instafix_url, post_id, media_index)
    try:
        session = await HTTPClient.get_session()
        async with session.head(
            media_url,
            timeout=_MEDIA_PROBE_TIMEOUT,
            headers=MediaProvider._DEFAULT_HEADERS,
            allow_redirects=False,
        ) as response:
            media = _media_from_probe(media_url, response)
            if media is not None:
                results[media_index - 1] = media
    except (TimeoutError, aiohttp.ClientError):
        return


def _media_from_probe(media_url: str, response: aiohttp.ClientResponse) -> InstaMedia | None:
    if 300 <= response.status < 400 and response.headers.get("Location"):
        return InstaMedia(url=media_url, kind=MediaKind.PHOTO)
    if response.status not in {200, 206}:
        return None

    content_type = response.headers.get("Content-Type", "").partition(";")[0].strip().casefold()
    if content_type.startswith("video/"):
        return InstaMedia(
            url=media_url,
            kind=MediaKind.VIDEO,
            thumbnail_url=f"{media_url}?thumbnail=1",
        )
    if content_type.startswith("image/"):
        return InstaMedia(url=media_url, kind=MediaKind.PHOTO)
    return None
