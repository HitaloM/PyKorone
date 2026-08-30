from typing import TYPE_CHECKING

from korone.modules.medias.download import DownloadOptions
from korone.modules.medias.models import MediaPost, MediaSource, ProviderInfo

from . import parser
from .constants import PATTERN, POST_PATTERN

if TYPE_CHECKING:
    from korone.modules.medias.download import MediaDownloader

    from .client import InstagramClient


class InstagramProvider:
    info = ProviderInfo(key="instagram", name="Instagram", website="Instagram", pattern=PATTERN, show_author_name=False)

    def __init__(self, client: InstagramClient, downloader: MediaDownloader) -> None:
        self._client = client
        self._downloader = downloader

    async def fetch(self, url: str) -> MediaPost | None:
        normalized_url = parser.ensure_url_scheme(url)
        if not POST_PATTERN.search(normalized_url):
            return None

        data = await self._client.get_data(parser.build_instafix_url(normalized_url))
        if not data:
            return None
        media = await self._downloader.download(
            tuple(MediaSource(item.kind, item.url, thumbnail_url=item.thumbnail_url) for item in data.media),
            options=DownloadOptions(filename_prefix="instagram", label=self.info.name),
        )
        if not media:
            return None

        username = data.username or ""
        return MediaPost(
            author_name=username,
            author_handle=username,
            text=data.description or "",
            url=parser.build_post_url(normalized_url),
            website=self.info.website,
            media=media,
        )
