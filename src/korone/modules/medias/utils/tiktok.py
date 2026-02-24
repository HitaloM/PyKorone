from __future__ import annotations

import gzip
import re
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import quote

import aiohttp
import orjson

from korone.constants import TELEGRAM_MEDIA_MAX_FILE_SIZE_BYTES
from korone.logger import get_logger
from korone.utils.aiohttp_session import HTTPClient

from .base import MediaKind, MediaPost, MediaProvider, MediaSource

if TYPE_CHECKING:
    from korone.utils.cached import JsonValue

    from .base import MediaItem

logger = get_logger(__name__)

TIKTOK_FEED_API = "https://api16-normal-c-useast1a.tiktokv.com/aweme/v1/feed/"
TIKTOK_IMAGE_AWEME_TYPES = {2, 68, 150}

TIKTOK_QUERY_PARAMS = {
    "iid": "7318518857994389254",
    "device_id": "7318517321748022790",
    "channel": "googleplay",
    "version_code": "300904",
    "device_platform": "android",
    "device_type": "ASUS_Z01QD",
    "os_version": "9",
    "aid": "1128",
}

TIKTOK_API_HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "identity",
    "Accept-Language": "en",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Sec-Ch-UA": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "Sec-Ch-UA-Mobile": "?0",
    "Sec-Ch-UA-Platform": '"Windows"',
}


class TikTokProvider(MediaProvider):
    name = "TikTok"
    website = "TikTok"
    pattern = re.compile(
        r"https?://(?:"
        r"(?:www\.|m\.)?tiktok\.com/(?:@[^/\s]+/(?:video|photo)/\d+|v/\d+|t/[A-Za-z0-9._-]+)"
        r"|(?:vm|vt)\.tiktok\.com/[A-Za-z0-9._-]+/?"
        r")(?:\?[^\s#]*)?(?:#[^\s]*)?",
        re.IGNORECASE,
    )
    _post_id_pattern = re.compile(r"/(?:video|photo|v)/(?P<id>\d+)", re.IGNORECASE)

    @classmethod
    async def fetch(cls, url: str) -> MediaPost | None:
        normalized_url = cls._ensure_url_scheme(url)
        post_id = await cls._resolve_post_id(normalized_url)
        if not post_id:
            return None

        aweme_payload = await cls._fetch_aweme(post_id)
        if not aweme_payload:
            return None

        aweme = cast("dict[str, Any]", aweme_payload)
        media_sources = cls._extract_media_sources(aweme)
        media = await cls._download_media(media_sources)
        if not media:
            return None

        author_name, author_handle = cls._extract_author(aweme)
        text = cls._extract_text(aweme)
        post_url = cls._extract_post_url(aweme, author_handle, post_id, normalized_url)

        return MediaPost(
            author_name=author_name or author_handle or "TikTok",
            author_handle=author_handle or "tiktok",
            text=text,
            url=post_url,
            website=cls.website,
            media=media,
        )

    @staticmethod
    def _ensure_url_scheme(url: str) -> str:
        if url.startswith(("http://", "https://")):
            return url
        return f"https://{url.lstrip('/')}"

    @classmethod
    async def _resolve_post_id(cls, url: str) -> str | None:
        post_id = cls._extract_post_id(url)
        if post_id:
            return post_id

        resolved_url = await cls._resolve_redirect_url(url)
        if not resolved_url:
            return None

        return cls._extract_post_id(resolved_url)

    @classmethod
    def _extract_post_id(cls, url: str) -> str | None:
        match = cls._post_id_pattern.search(url)
        if not match:
            return None
        post_id = match.group("id")
        return post_id if post_id.isdigit() else None

    @classmethod
    async def _resolve_redirect_url(cls, url: str) -> str | None:
        try:
            session = await HTTPClient.get_session()
            async with session.get(
                url, timeout=cls._DEFAULT_TIMEOUT, headers=cls._DEFAULT_HEADERS, allow_redirects=True, max_redirects=2
            ) as response:
                return str(response.url)
        except aiohttp.ClientError as exc:
            await logger.aerror("[TikTok] Redirect resolution failed", error=str(exc), url=url)
            return None

    @classmethod
    async def _fetch_aweme(cls, post_id: str) -> dict[str, JsonValue] | None:
        params = {**TIKTOK_QUERY_PARAMS, "aweme_id": post_id}
        headers = {**cls._DEFAULT_HEADERS, **TIKTOK_API_HEADERS}

        methods = ("OPTIONS", "GET")
        for method in methods:
            try:
                session = await HTTPClient.get_session()
                async with session.request(
                    method, TIKTOK_FEED_API, timeout=cls._DEFAULT_TIMEOUT, headers=headers, params=params
                ) as response:
                    if response.status != 200:
                        await logger.adebug(
                            "[TikTok] Non-200 feed response", method=method, status=response.status, post_id=post_id
                        )
                        continue

                    payload = cls._load_feed_payload(await response.read())
            except (
                aiohttp.ClientError,
                aiohttp.ContentTypeError,
                orjson.JSONDecodeError,
                UnicodeDecodeError,
                OSError,
            ) as exc:
                await logger.aerror("[TikTok] Feed request failed", method=method, error=str(exc), post_id=post_id)
                continue

            if not isinstance(payload, dict):
                continue

            aweme = cls._extract_first_aweme(payload, post_id)
            if aweme:
                return cast("dict[str, JsonValue]", aweme)

        return None

    @classmethod
    def _load_feed_payload(cls, payload: bytes) -> Any:  # noqa: ANN401
        # Some TikTok edges return gzipped bytes without a matching response header.
        if cls._is_gzip_payload(payload):
            payload = gzip.decompress(payload)
        return orjson.loads(payload)

    @staticmethod
    def _is_gzip_payload(payload: bytes) -> bool:
        return len(payload) >= 2 and payload[0] == 0x1F and payload[1] == 0x8B

    @classmethod
    def _extract_first_aweme(cls, payload: dict[str, Any], post_id: str) -> dict[str, Any] | None:
        aweme_list_raw = payload.get("aweme_list")
        if not isinstance(aweme_list_raw, list) or not aweme_list_raw:
            return None

        first_aweme = aweme_list_raw[0]
        if not isinstance(first_aweme, dict):
            return None

        aweme_id_raw = first_aweme.get("aweme_id")
        aweme_id = str(aweme_id_raw).strip() if aweme_id_raw is not None else ""
        if aweme_id != post_id:
            return None

        return first_aweme

    @classmethod
    def _extract_media_sources(cls, aweme: dict[str, Any]) -> list[MediaSource]:
        aweme_type = cls._coerce_int(aweme.get("aweme_type"))
        if aweme_type in TIKTOK_IMAGE_AWEME_TYPES:
            image_sources = cls._extract_image_sources(aweme)
            if image_sources:
                return image_sources

        video_sources = cls._extract_video_sources(aweme)
        if video_sources:
            return video_sources

        return cls._extract_image_sources(aweme)

    @classmethod
    def _extract_image_sources(cls, aweme: dict[str, Any]) -> list[MediaSource]:
        image_post_info = aweme.get("image_post_info")
        if not isinstance(image_post_info, dict):
            return []

        images_raw = image_post_info.get("images")
        if not isinstance(images_raw, list):
            return []

        sources: list[MediaSource] = []
        seen: set[str] = set()
        for image_raw in images_raw:
            if not isinstance(image_raw, dict):
                continue

            display_image = image_raw.get("display_image")
            display = display_image if isinstance(display_image, dict) else {}
            thumbnail_image = image_raw.get("thumbnail")
            thumbnail = thumbnail_image if isinstance(thumbnail_image, dict) else {}

            image_url = cls._pick_url(display.get("url_list"), preferred_index=1)
            if not image_url or image_url in seen:
                continue

            seen.add(image_url)
            thumbnail_url = cls._pick_url(thumbnail.get("url_list"), preferred_index=0)
            sources.append(MediaSource(kind=MediaKind.PHOTO, url=image_url, thumbnail_url=thumbnail_url))

        return sources

    @classmethod
    def _extract_video_sources(cls, aweme: dict[str, Any]) -> list[MediaSource]:
        video_raw = aweme.get("video")
        video = video_raw if isinstance(video_raw, dict) else {}

        play_addr_raw = video.get("play_addr")
        play_addr = play_addr_raw if isinstance(play_addr_raw, dict) else {}
        cover_raw = video.get("cover")
        cover = cover_raw if isinstance(cover_raw, dict) else {}

        video_url = cls._pick_url(play_addr.get("url_list"), preferred_index=0)
        if not video_url:
            return []

        duration_ms = cls._coerce_int(video.get("duration"))
        duration = duration_ms // 1000 if isinstance(duration_ms, int) and duration_ms > 0 else None

        width = cls._coerce_int(play_addr.get("width")) or cls._coerce_int(video.get("width"))
        height = cls._coerce_int(play_addr.get("height")) or cls._coerce_int(video.get("height"))

        return [
            MediaSource(
                kind=MediaKind.VIDEO,
                url=video_url,
                thumbnail_url=cls._pick_url(cover.get("url_list"), preferred_index=0),
                duration=duration,
                width=width,
                height=height,
            )
        ]

    @staticmethod
    def _pick_url(url_list: object, *, preferred_index: int) -> str | None:
        if not isinstance(url_list, list):
            return None

        candidates = [value.strip() for value in url_list if isinstance(value, str) and value.strip()]
        if not candidates:
            return None

        if 0 <= preferred_index < len(candidates):
            return candidates[preferred_index]
        return candidates[0]

    @staticmethod
    def _extract_author(aweme: dict[str, Any]) -> tuple[str, str]:
        author_raw = aweme.get("author")
        author = author_raw if isinstance(author_raw, dict) else {}

        nickname = author.get("nickname")
        unique_id = author.get("unique_id")

        author_name = str(nickname).strip() if isinstance(nickname, str) else ""
        author_handle = str(unique_id).strip().lstrip("@") if isinstance(unique_id, str) else ""

        if not author_handle and author_name:
            author_handle = author_name.lstrip("@")

        return author_name, author_handle

    @staticmethod
    def _extract_text(aweme: dict[str, Any]) -> str:
        description = aweme.get("desc")
        return str(description).strip() if isinstance(description, str) else ""

    @staticmethod
    def _extract_post_url(aweme: dict[str, Any], author_handle: str, post_id: str, fallback_url: str) -> str:
        share_url = aweme.get("share_url")
        if isinstance(share_url, str) and share_url.startswith(("https://", "http://")):
            return share_url

        if author_handle:
            return f"https://www.tiktok.com/@{quote(author_handle)}/video/{quote(post_id)}"

        return fallback_url

    @staticmethod
    def _coerce_int(value: object) -> int | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            try:
                return int(float(value))
            except ValueError:
                return None
        return None

    @classmethod
    async def _download_media(cls, sources: list[MediaSource]) -> list[MediaItem]:
        return await cls.download_media(
            sources, filename_prefix="tiktok_media", max_size=TELEGRAM_MEDIA_MAX_FILE_SIZE_BYTES, log_label="TikTok"
        )
