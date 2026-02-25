from __future__ import annotations

from typing import TYPE_CHECKING

from korone.constants import TELEGRAM_MEDIA_MAX_FILE_SIZE_BYTES
from korone.modules.medias.utils.provider_base import MediaProvider
from korone.modules.medias.utils.types import MediaPost

from . import client, parser
from .constants import PATTERN

if TYPE_CHECKING:
    from korone.modules.medias.utils.types import MediaItem, MediaSource


class BlueskyProvider(MediaProvider):
    name = "Bluesky"
    website = "Bluesky"
    pattern = PATTERN

    @classmethod
    async def fetch(cls, url: str) -> MediaPost | None:
        handle, rkey = parser.extract_handle_and_rkey(url, cls.pattern)
        if not handle or not rkey:
            return None

        did = await client.resolve_handle(handle)
        if not did:
            return None

        uri = f"at://{did}/app.bsky.feed.post/{rkey}"
        thread = await client.get_post_thread(uri)
        if not thread:
            return None

        post = parser.extract_post(thread)
        if not post:
            return None

        author_name, author_handle, author_did = parser.extract_author(post)
        text = parser.extract_text(post)
        post_url = parser.build_post_url(author_handle or handle, rkey)

        effective_did = author_did or did
        embed_view, embed_type = parser.extract_embed_view(post)
        if not embed_view or not embed_type:
            return None

        pds_url = None
        if embed_type == "app.bsky.embed.video#view":
            pds_url = await client.resolve_pds_url(effective_did)
            if not pds_url:
                return None

        media_sources = parser.extract_media_sources(embed_view, embed_type, effective_did, pds_url)
        media = await cls._download_media(media_sources)
        if not media:
            return None

        return MediaPost(
            author_name=author_name or author_handle or "Bluesky",
            author_handle=author_handle or handle,
            text=text,
            url=post_url,
            website=cls.website,
            media=media,
        )

    @classmethod
    async def _download_media(cls, sources: list[MediaSource]) -> list[MediaItem]:
        return await cls.download_media(
            sources, filename_prefix="bsky_media", max_size=TELEGRAM_MEDIA_MAX_FILE_SIZE_BYTES, log_label="Bluesky"
        )
