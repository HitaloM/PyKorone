from __future__ import annotations

from typing import TYPE_CHECKING

from korone.modules.medias.utils.provider_base import MediaProvider
from korone.modules.medias.utils.types import MediaPost

from . import client, parser
from .constants import FXTWITTER_API, PATTERN

if TYPE_CHECKING:
    from korone.modules.medias.utils.types import MediaItem, MediaSource


class TwitterProvider(MediaProvider):
    name = "Twitter"
    website = "Twitter"
    pattern = PATTERN

    @classmethod
    async def fetch(cls, url: str) -> MediaPost | None:
        status_id, handle = parser.extract_status_id_and_handle(url)
        if not status_id:
            return None

        data = await client.fetch_json(FXTWITTER_API.format(status_id=status_id))
        if not data:
            return None

        tweet = parser.extract_tweet_payload(data)
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
