from typing import TYPE_CHECKING

from korone.modules.medias.download import DownloadOptions
from korone.modules.medias.models import MediaPost, ProviderInfo

from . import parser
from .constants import PATTERN

if TYPE_CHECKING:
    from korone.modules.medias.download import MediaDownloader

    from .client import BlueskyClient


class BlueskyProvider:
    info = ProviderInfo(key="bluesky", name="Bluesky", website="Bluesky", pattern=PATTERN)

    def __init__(self, client: BlueskyClient, downloader: MediaDownloader) -> None:
        self._client = client
        self._downloader = downloader

    async def fetch(self, url: str) -> MediaPost | None:
        handle, rkey = parser.extract_handle_and_rkey(url, self.info.pattern)
        if not handle or not rkey or not (did := await self._client.resolve_handle(handle)):
            return None

        thread = await self._client.get_post_thread(f"at://{did}/app.bsky.feed.post/{rkey}")
        if not thread or not (post := parser.extract_post(thread)):
            return None

        author_name, author_handle, author_did = parser.extract_author(post)
        effective_did = author_did or did
        embed_view, embed_type = parser.extract_embed_view(post)
        if not embed_view or not embed_type:
            return None

        pds_url = None
        if embed_type == "app.bsky.embed.video#view":
            pds_url = await self._client.resolve_pds_url(effective_did)
            if not pds_url:
                return None

        media = await self._downloader.download(
            parser.extract_media_sources(embed_view, embed_type, effective_did, pds_url),
            options=DownloadOptions(filename_prefix="bsky_media", label=self.info.name),
        )
        if not media:
            return None

        return MediaPost(
            author_name=author_name or author_handle or "",
            author_handle=author_handle or handle,
            text=parser.extract_text(post),
            url=parser.build_post_url(author_handle or handle, rkey),
            website=self.info.website,
            media=media,
        )
