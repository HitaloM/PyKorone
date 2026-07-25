from korone.modules.medias.utils.provider_base import MediaProvider
from korone.modules.medias.utils.types import MediaPost, MediaSource

from . import client, parser
from .constants import PATTERN, POST_PATTERN


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
        data = await client.get_instafix_data(instafix_url)
        if not data:
            return None

        sources = [
            MediaSource(kind=media.kind, url=media.url, thumbnail_url=media.thumbnail_url) for media in data.media
        ]
        media_items = await cls.download_media(sources, filename_prefix="instagram")
        if not media_items:
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
            media=media_items,
        )
