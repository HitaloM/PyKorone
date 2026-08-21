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
        if not post_id or not (payload := await client.fetch_post(post_id, headers=cls._API_HEADERS)):
            return None

        media = await cls.download_media(parser.extract_media_sources(payload), filename_prefix="example_media")
        if not media:
            return None

        author_name, author_handle = parser.extract_author(payload)
        return MediaPost(
            author_name=author_name or cls.name,
            author_handle=author_handle or cls.name.casefold(),
            text=parser.extract_text(payload),
            url=url,
            website=cls.website,
            media=media,
        )
