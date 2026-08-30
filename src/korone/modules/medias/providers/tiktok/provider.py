from dataclasses import replace
from typing import TYPE_CHECKING

from korone.logger import get_logger
from korone.modules.medias.download import DownloadOptions
from korone.modules.medias.models import MediaKind, MediaPost, MediaSource, PreparedMedia, ProviderInfo
from korone.modules.medias.parsing import ensure_url_scheme

from . import parser
from .constants import PATTERN, TIKTOK_MEDIA_HEADERS, TIKTOK_TIMEOUT

if TYPE_CHECKING:
    from korone.modules.medias.download import MediaDownloader

    from .client import TikTokClient

_OFFLOAD_BASE_URL = "https://offload.tnktok.com"
logger = get_logger(__name__)


class TikTokProvider:
    info = ProviderInfo(key="tiktok", name="TikTok", website="TikTok", pattern=PATTERN)

    def __init__(self, client: TikTokClient, downloader: MediaDownloader) -> None:
        self._client = client
        self._downloader = downloader

    async def fetch(self, url: str) -> MediaPost | None:
        normalized_url = ensure_url_scheme(url)
        post_id, resolved_url = await self._resolve_post_id(normalized_url)
        if not post_id or not (item_struct := await self._client.fetch_item_struct(post_id)):
            return None

        sources = await self._extract_sources(item_struct)
        media = await self._download(sources, post_id=post_id)
        if not media:
            return None

        author_name, author_handle = parser.extract_author(item_struct)
        return MediaPost(
            author_name=author_name or author_handle or "",
            author_handle=author_handle or "",
            text=parser.extract_text(item_struct),
            url=parser.build_post_url(item_struct, resolved_url or normalized_url),
            website=self.info.website,
            media=media,
        )

    async def _resolve_post_id(self, url: str) -> tuple[str | None, str | None]:
        if post_id := parser.extract_post_id(url):
            return post_id, url
        resolved_url = await self._client.resolve_redirect_url(url)
        return (parser.extract_post_id(resolved_url), resolved_url) if resolved_url else (None, None)

    async def _extract_sources(self, item_struct: dict[str, object]) -> tuple[MediaSource, ...]:
        sources = tuple(parser.extract_media_sources(item_struct))
        if len(sources) != 1 or sources[0].kind != MediaKind.VIDEO:
            return sources
        source = sources[0]
        resolved_url = await self._client.resolve_media_url(source.url)
        return (replace(source, url=resolved_url),) if resolved_url and resolved_url != source.url else sources

    async def _download(self, sources: tuple[MediaSource, ...], *, post_id: str) -> tuple[PreparedMedia, ...]:
        options = DownloadOptions(
            filename_prefix="tiktok_media",
            label=self.info.name,
            headers=dict(TIKTOK_MEDIA_HEADERS),
            timeout=TIKTOK_TIMEOUT,
        )
        if media := await self._downloader.download(sources, options=options):
            return media

        offload_media = await self._downloader.download(
            self._build_offload_sources(post_id, sources), options=replace(options, label="TikTok Offload")
        )
        if offload_media:
            await logger.adebug(
                "[TikTok] Using downloaded offload fallback",
                source_count=len(offload_media),
                offload_url=_OFFLOAD_BASE_URL,
            )
        return offload_media

    @staticmethod
    def _build_offload_sources(post_id: str, sources: tuple[MediaSource, ...]) -> tuple[MediaSource, ...]:
        photo_index = 1
        fallback: list[MediaSource] = []
        for source in sources:
            if source.kind == MediaKind.VIDEO:
                offload_url = f"{_OFFLOAD_BASE_URL}/generate/video/{post_id}.mp4"
            else:
                offload_url = f"{_OFFLOAD_BASE_URL}/generate/image/{post_id}/{photo_index}"
                photo_index += 1
            fallback.append(replace(source, url=offload_url))
        return tuple(fallback)
