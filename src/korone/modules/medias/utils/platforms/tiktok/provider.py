from __future__ import annotations

from typing import TYPE_CHECKING

from korone.constants import TELEGRAM_MEDIA_MAX_FILE_SIZE_BYTES
from korone.modules.medias.utils.platforms import MediaProvider
from korone.modules.medias.utils.types import MediaPost

from . import client, parser
from .constants import PATTERN

if TYPE_CHECKING:
    from korone.modules.medias.utils.types import MediaItem, MediaSource


class TikTokProvider(MediaProvider):
    name = "TikTok"
    website = "TikTok"
    pattern = PATTERN

    @classmethod
    async def fetch(cls, url: str) -> MediaPost | None:
        normalized_url = parser.ensure_url_scheme(url)
        post_id = await cls._resolve_post_id(normalized_url)
        if not post_id:
            return None

        aweme = await client.fetch_aweme(post_id)
        if not aweme:
            return None

        media_sources = parser.extract_media_sources(aweme)
        media = await cls._download_media(media_sources)
        if not media:
            return None

        author_name, author_handle = parser.extract_author(aweme)
        text = parser.extract_text(aweme)
        post_url = parser.extract_post_url(aweme, author_handle, post_id, normalized_url)

        return MediaPost(
            author_name=author_name or author_handle or "TikTok",
            author_handle=author_handle or "tiktok",
            text=text,
            url=post_url,
            website=cls.website,
            media=media,
        )

    @classmethod
    async def _resolve_post_id(cls, url: str) -> str | None:
        post_id = parser.extract_post_id(url)
        if post_id:
            return post_id

        resolved_url = await client.resolve_redirect_url(url)
        if not resolved_url:
            return None

        return parser.extract_post_id(resolved_url)

    @classmethod
    async def _download_media(cls, sources: list[MediaSource]) -> list[MediaItem]:
        return await cls.download_media(
            sources, filename_prefix="tiktok_media", max_size=TELEGRAM_MEDIA_MAX_FILE_SIZE_BYTES, log_label="TikTok"
        )
