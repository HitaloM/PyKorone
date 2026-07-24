from typing import ClassVar

from korone.modules.medias.utils.provider_base import MediaProvider
from korone.modules.medias.utils.types import MediaPost

from . import client, parser
from .constants import PATTERN, REQUEST_TIMEOUT


class ExampleProvider(MediaProvider):
    name = "Example"
    website = "Example"
    pattern = PATTERN
    _DEFAULT_TIMEOUT = REQUEST_TIMEOUT
    _API_HEADERS: ClassVar[dict[str, str]] = {**MediaProvider._DEFAULT_HEADERS, "Accept": "application/json"}

    @classmethod
    async def fetch(cls, url: str) -> MediaPost | None:
        post_id = parser.extract_post_id(url)
        if not post_id:
            return None

        payload = await client.fetch_post(post_id, headers=cls._API_HEADERS)
        if not payload:
            return None

        media = await cls.download_media(
            parser.extract_media_sources(payload), filename_prefix="example_media", log_label=cls.name
        )
        if not media:
            return None

        author_handle = parser.extract_author(payload)
        return MediaPost(
            author_name=author_handle or cls.name,
            author_handle=author_handle or "example",
            text=parser.extract_text(payload),
            url=url,
            website=cls.website,
            media=media,
        )
