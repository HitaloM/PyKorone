from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, cast

import aiohttp

from korone.constants import CACHE_MEDIA_TTL_SECONDS
from korone.logger import get_logger
from korone.utils.cached import Cached

from .base import MediaKind, MediaPost, MediaProvider, MediaSource

if TYPE_CHECKING:
    from korone.utils.cached import JsonValue

    from .base import MediaItem

logger = get_logger(__name__)

FXTWITTER_API = "https://api.fxtwitter.com/status/{status_id}"
HTTP_TIMEOUT = 25


class FXTwitterProvider(MediaProvider):
    name = "Twitter"
    website = "Twitter"
    pattern = re.compile(
        r"https?://(?:www\.)?(?:x\.com|twitter\.com)/(?:i/web/)?(?:[A-Za-z0-9_]{1,15}/)?status/\d+(?:/[^\s?]+)?(?:\?[^\s]+)?",
        re.IGNORECASE,
    )

    @classmethod
    async def fetch(cls, url: str) -> MediaPost | None:
        status_id, handle = cls._extract_status_id_and_handle(url)
        if not status_id:
            return None

        api_url = FXTWITTER_API.format(status_id=status_id)
        data = await cls._fetch_json(api_url)
        if not data:
            return None

        tweet = cls._extract_tweet_payload(data)
        if not tweet:
            return None

        author_name, author_handle = cls._extract_author(tweet)
        if handle and not author_handle:
            author_handle = handle

        text = cls._extract_text(tweet)
        post_url = cls._extract_post_url(tweet, status_id, author_handle, url)

        media_sources = cls._extract_media_sources(tweet)
        media = await cls._download_media(media_sources)
        if not media:
            return None

        return MediaPost(
            author_name=author_name or author_handle or "X",
            author_handle=author_handle or "",
            text=text,
            url=post_url,
            website=cls.website,
            media=media,
        )

    @staticmethod
    def _extract_status_id_and_handle(url: str) -> tuple[str | None, str | None]:
        match = re.search(
            r"https?://(?:www\.)?(?:x\.com|twitter\.com)/(?:i/web/)?(?:(?P<handle>[A-Za-z0-9_]{1,15})/)?status/(?P<id>\d+)",
            url,
            re.IGNORECASE,
        )
        if not match:
            return None, None
        status_id = match.group("id")
        handle = match.group("handle")
        return status_id, handle

    @staticmethod
    @Cached(ttl=CACHE_MEDIA_TTL_SECONDS, key="fxtwitter:json")
    async def _fetch_json(url: str) -> dict[str, JsonValue] | None:
        timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT)
        headers = {"accept": "application/json", "user-agent": "KoroneBot/1.0"}
        try:
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session, session.get(url) as response:
                if response.status != 200:
                    await logger.adebug("[FXTwitter] Non-200 response", status=response.status, url=url)
                    return None
                data = await response.json()
                return cast("dict[str, JsonValue]", data)
        except (aiohttp.ClientError, aiohttp.ContentTypeError) as exc:
            await logger.aerror("[FXTwitter] Request error", error=str(exc))
            return None

    @staticmethod
    def _extract_tweet_payload(data: dict[str, Any]) -> dict[str, Any] | None:
        if "tweet" in data and isinstance(data["tweet"], dict):
            return data["tweet"]
        if "data" in data and isinstance(data["data"], dict):
            return data["data"]
        if "tweet" not in data and "data" not in data:
            return data
        return None

    @staticmethod
    def _extract_author(tweet: dict[str, Any]) -> tuple[str, str]:
        author = tweet.get("author") or tweet.get("user") or {}
        author_name = author.get("name") or tweet.get("author_name") or tweet.get("user_name") or ""
        author_handle = (
            author.get("screen_name")
            or author.get("username")
            or tweet.get("author_handle")
            or tweet.get("user_screen_name")
            or ""
        )
        author_handle = author_handle.lstrip("@") if author_handle else ""
        return str(author_name), str(author_handle)

    @staticmethod
    def _extract_text(tweet: dict[str, Any]) -> str:
        text = tweet.get("text") or tweet.get("full_text") or tweet.get("content") or ""
        return str(text)

    @staticmethod
    def _extract_post_url(tweet: dict[str, Any], status_id: str, handle: str | None, fallback: str) -> str:
        url = tweet.get("url") or tweet.get("tweet_url") or ""
        if url:
            return str(url)
        if handle:
            return f"https://x.com/{handle}/status/{status_id}"
        return fallback

    @classmethod
    def _extract_media_sources(cls, tweet: dict[str, Any]) -> list[MediaSource]:
        media = tweet.get("media") or {}
        sources: list[MediaSource] = []
        seen: set[str] = set()

        def _ensure_list(value: object) -> list[dict[str, Any]]:
            if isinstance(value, list):
                return [cast("dict[str, Any]", item) for item in value if isinstance(item, dict)]
            if isinstance(value, dict):
                return [cast("dict[str, Any]", value)]
            return []

        def _add(kind: MediaKind, url: str) -> None:
            if not url or url in seen:
                return
            seen.add(url)
            sources.append(MediaSource(kind=kind, url=url))

        for photo in _ensure_list(media.get("photos")) + _ensure_list(media.get("images")):
            url = photo.get("url") or photo.get("src") or photo.get("source")
            if isinstance(url, str):
                _add(MediaKind.PHOTO, url)

        for video in _ensure_list(media.get("videos")) + _ensure_list(media.get("video")):
            url = cls._pick_video_url(video)
            if url:
                _add(MediaKind.VIDEO, url)

        for item in _ensure_list(media.get("all")):
            url = item.get("url") or item.get("src") or item.get("source")
            if not isinstance(url, str):
                continue
            kind = MediaKind.VIDEO if item.get("type") in {"video", "gif"} else MediaKind.PHOTO
            _add(kind, url)

        if not sources:
            media_url = tweet.get("media_url") or tweet.get("media_url_https")
            if isinstance(media_url, str):
                _add(MediaKind.PHOTO, media_url)

        return sources

    @staticmethod
    def _pick_video_url(video: dict[str, Any]) -> str | None:
        direct_url = video.get("url") or video.get("src") or video.get("source")
        if isinstance(direct_url, str):
            return direct_url

        variants = video.get("variants")
        if not isinstance(variants, list):
            return None

        best_url = None
        best_bitrate = -1
        for variant in variants:
            url = variant.get("url")
            if not isinstance(url, str):
                continue
            bitrate = variant.get("bitrate")
            if isinstance(bitrate, int) and bitrate > best_bitrate:
                best_bitrate = bitrate
                best_url = url
            if best_url is None:
                best_url = url
        return best_url

    @classmethod
    async def _download_media(cls, sources: list[MediaSource]) -> list[MediaItem]:
        return await cls._download_media_sources(
            sources, timeout=HTTP_TIMEOUT, filename_prefix="x_media", log_label="FXTwitter"
        )
