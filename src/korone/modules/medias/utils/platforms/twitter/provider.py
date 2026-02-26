from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import quote

from korone.logger import get_logger
from korone.modules.medias.utils.provider_base import MediaProvider
from korone.modules.medias.utils.types import MediaPost

from . import client, parser
from .constants import FXTWITTER_STATUS_API, FXTWITTER_STATUS_API_WITH_HANDLE, PATTERN

if TYPE_CHECKING:
    from typing import Any

    from korone.modules.medias.utils.types import MediaItem, MediaSource

logger = get_logger(__name__)


class TwitterProvider(MediaProvider):
    name = "Twitter"
    website = "Twitter"
    pattern = PATTERN

    @classmethod
    async def fetch(cls, url: str) -> MediaPost | None:
        status_id, handle = parser.extract_status_id_and_handle(url)
        if not status_id:
            return None

        tweet = await cls._fetch_tweet(status_id, handle)
        if not tweet:
            return None

        author_name, author_handle = parser.extract_author(tweet)
        if handle and not author_handle:
            author_handle = handle

        text = parser.extract_text(tweet)
        post_url = parser.extract_post_url(tweet, status_id, author_handle, url)

        media_sources = parser.extract_media_sources(tweet)
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

    @classmethod
    async def _download_media(cls, sources: list[MediaSource]) -> list[MediaItem]:
        return await cls.download_media(sources, filename_prefix="x_media", log_label="FXTwitter")

    @classmethod
    async def _fetch_tweet(cls, status_id: str, handle: str | None) -> dict[str, Any] | None:
        for endpoint in cls._build_status_endpoints(status_id, handle):
            payload = await client.fetch_json(endpoint)
            if not payload:
                continue

            tweet = parser.extract_tweet_payload(payload)
            if tweet:
                return tweet

            await logger.adebug(
                "[FXTwitter] Missing tweet payload",
                status_code=parser.extract_status_code(payload),
                status_message=parser.extract_status_message(payload),
                endpoint=endpoint,
            )
        return None

    @staticmethod
    def _build_status_endpoints(status_id: str, handle: str | None) -> list[str]:
        endpoints: list[str] = []
        if handle:
            endpoints.append(
                FXTWITTER_STATUS_API_WITH_HANDLE.format(handle=quote(handle, safe=""), status_id=quote(status_id))
            )

        endpoints.append(FXTWITTER_STATUS_API.format(status_id=quote(status_id)))

        unique_endpoints: list[str] = []
        seen: set[str] = set()
        for endpoint in endpoints:
            if endpoint in seen:
                continue
            seen.add(endpoint)
            unique_endpoints.append(endpoint)
        return unique_endpoints
