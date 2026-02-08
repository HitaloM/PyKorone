from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import aiohttp
from aiogram.types import BufferedInputFile
from lxml import html as lxml_html

from korone.constants import CACHE_MEDIA_TTL_SECONDS
from korone.logger import get_logger
from korone.utils.aiohttp_session import HTTPClient
from korone.utils.cached import Cached

from .base import MediaItem, MediaKind, MediaPost, MediaProvider

logger = get_logger(__name__)

INSTAGRAM_HOST = "instagram.com"
INSTAFIX_HOST = "eeinstagram.com"


@dataclass(frozen=True, slots=True)
class _InstaData:
    media_url: str
    username: str
    description: str
    media_type: str


class InstagramProvider(MediaProvider):
    name = "Instagram"
    website = "Instagram"
    pattern = re.compile(
        r"https?://(?:www\.)?(?:instagram\.com|eeinstagram\.com)/(?:reel(?:s?)|p|tv)/[A-Za-z0-9_-]+(?:/[\w-]+)?(?:\?[^\s]+)?",
        re.IGNORECASE,
    )
    post_pattern = re.compile(r"(?:reel(?:s?)|p|tv)/(?P<post_id>[A-Za-z0-9_-]+)", re.IGNORECASE)

    @classmethod
    async def fetch(cls, url: str) -> MediaPost | None:
        normalized_url = cls._ensure_url_scheme(url)
        if not cls.post_pattern.search(normalized_url):
            return None

        instafix_url = cls._build_instafix_url(normalized_url)
        data_raw = await cls._get_instafix_data(instafix_url)
        if not data_raw or not data_raw.get("media_url"):
            return None

        data = _InstaData(
            media_url=data_raw.get("media_url", ""),
            username=data_raw.get("username", ""),
            description=data_raw.get("description", ""),
            media_type=data_raw.get("media_type", ""),
        )

        media_kind = MediaKind.VIDEO if data.media_type == "video" else MediaKind.PHOTO
        media_item = await cls._download_media(data.media_url, media_kind)
        if not media_item:
            return None

        author_name = data.username or "Instagram"
        author_handle = data.username or "instagram"
        post_url = cls._build_post_url(normalized_url)

        return MediaPost(
            author_name=author_name,
            author_handle=author_handle,
            text=data.description or "",
            url=post_url,
            website=cls.website,
            media=[media_item],
        )

    @staticmethod
    def _ensure_url_scheme(url: str) -> str:
        if url.startswith(("http://", "https://")):
            return url
        return f"https://{url.lstrip('/')}"

    @staticmethod
    def _build_instafix_url(url: str) -> str:
        if INSTAFIX_HOST in url:
            return url
        return url.replace(INSTAGRAM_HOST, INSTAFIX_HOST)

    @staticmethod
    def _build_post_url(url: str) -> str:
        if INSTAFIX_HOST in url:
            return url.replace(INSTAFIX_HOST, INSTAGRAM_HOST)
        return url

    @classmethod
    @Cached(ttl=CACHE_MEDIA_TTL_SECONDS, key="instafix:html")
    async def _get_instafix_data(cls, instafix_url: str) -> dict[str, str] | None:
        try:
            session = await HTTPClient.get_session()
            async with session.get(
                instafix_url, timeout=cls._DEFAULT_TIMEOUT, headers=cls._DEFAULT_HEADERS, allow_redirects=True
            ) as response:
                if response.status != 200:
                    await logger.adebug("[Instagram] Non-200 response", status=response.status, url=instafix_url)
                    return None

                text = await response.text()
                scraped = cls._scrape_instafix_data(text)
                if not scraped.get("media_url"):
                    return None

                media_url = cls._ensure_url_scheme(scraped["media_url"])
                async with session.get(media_url, allow_redirects=True) as media_response:
                    if media_response.status != 200:
                        await logger.adebug(
                            "[Instagram] Media redirect failed", status=media_response.status, url=media_url
                        )
                        return None
                    media_url = str(media_response.url)
                    await media_response.release()

                scraped["media_url"] = media_url
                scraped["media_type"] = scraped.get("type", "")
                scraped.pop("type", None)
                return scraped
        except (aiohttp.ClientError, aiohttp.ContentTypeError) as exc:
            await logger.aerror("[Instagram] Fetch failed", error=str(exc), url=instafix_url)
            return None

    @classmethod
    def _scrape_instafix_data(cls, html_content: str) -> dict[str, str]:
        tree = lxml_html.fromstring(html_content)
        meta_nodes = tree.xpath("//head/meta[@property or @name]")
        scraped: dict[str, str] = {"media_url": "", "username": "", "description": "", "type": ""}

        for node in meta_nodes:
            prop = node.get("property") or node.get("name")
            content = node.get("content")
            if not prop or not content:
                continue

            if prop == "og:video":
                scraped["type"] = "video"
                scraped["media_url"] = cls._build_instafix_media_url(content)
            elif prop == "twitter:title":
                scraped["username"] = content.lstrip("@").strip()
            elif prop == "og:description":
                scraped["description"] = html.unescape(content).strip()
            elif prop == "og:image" and not scraped["media_url"]:
                scraped["type"] = "photo"
                image_url = content.replace("/images/", "/grid/")
                image_url = re.sub(r"/\d+$", "/", image_url)
                scraped["media_url"] = cls._build_instafix_media_url(image_url)

        return scraped

    @staticmethod
    def _build_instafix_media_url(path_or_url: str) -> str:
        if path_or_url.startswith(("http://", "https://")):
            return path_or_url
        return f"https://{INSTAFIX_HOST}{path_or_url}"

    @classmethod
    async def _download_media(cls, url: str, kind: MediaKind) -> MediaItem | None:
        try:
            session = await HTTPClient.get_session()
            async with session.get(url, timeout=cls._DEFAULT_TIMEOUT, headers=cls._DEFAULT_HEADERS) as response:
                if response.status != 200:
                    await logger.adebug("[Instagram] Failed to download media", status=response.status, url=url)
                    return None
                payload = await response.read()
        except aiohttp.ClientError as exc:
            await logger.aerror("[Instagram] Media download error", error=str(exc))
            return None

        filename = cls._make_filename(url, kind)
        return MediaItem(kind=kind, file=BufferedInputFile(payload, filename), filename=filename)

    @staticmethod
    def _make_filename(url: str, kind: MediaKind) -> str:
        parsed = urlparse(url)
        suffix = Path(parsed.path).suffix
        if not suffix:
            suffix = ".mp4" if kind == MediaKind.VIDEO else ".jpg"
        return f"instagram_media{suffix}"
