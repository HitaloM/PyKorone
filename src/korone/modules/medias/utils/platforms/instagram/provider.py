from __future__ import annotations

from aiogram.types import BufferedInputFile

from korone.modules.medias.utils.provider_base import MediaProvider
from korone.modules.medias.utils.types import MediaItem, MediaKind, MediaPost

from . import client, parser
from .constants import PATTERN, POST_PATTERN
from .types import InstaData


class InstagramProvider(MediaProvider):
    name = "Instagram"
    website = "Instagram"
    pattern = PATTERN
    post_pattern = POST_PATTERN

    @classmethod
    async def fetch(cls, url: str) -> MediaPost | None:
        normalized_url = parser.ensure_url_scheme(url)
        if not cls.post_pattern.search(normalized_url):
            return None

        instafix_url = parser.build_instafix_url(normalized_url)
        data_raw = await client.get_instafix_data(instafix_url)
        if not data_raw or not data_raw.get("media_url"):
            return None

        data = InstaData(
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
        post_url = parser.build_post_url(normalized_url)

        return MediaPost(
            author_name=author_name,
            author_handle=author_handle,
            text=data.description or "",
            url=post_url,
            website=cls.website,
            media=[media_item],
        )

    @classmethod
    async def _download_media(cls, url: str, kind: MediaKind) -> MediaItem | None:
        payload = await client.download_media(url)
        if payload is None:
            return None

        filename = parser.make_filename(url, kind)
        return MediaItem(kind=kind, file=BufferedInputFile(payload, filename), filename=filename, source_url=url)
