from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from korone.constants import TELEGRAM_MEDIA_MAX_FILE_SIZE_BYTES
from korone.logger import get_logger
from korone.modules.medias.utils.provider_base import MediaProvider
from korone.modules.medias.utils.types import MediaKind, MediaPost, MediaSource

from . import client, parser
from .constants import PATTERN, TIKTOK_MEDIA_HEADERS

if TYPE_CHECKING:
    from korone.modules.medias.utils.types import MediaItem

_TNKTOK_OFFLOAD_BASE_URL = "https://offload.tnktok.com"

logger = get_logger(__name__)


class TikTokProvider(MediaProvider):
    name = "TikTok"
    website = "TikTok"
    pattern = PATTERN
    _DEFAULT_HEADERS: ClassVar[dict[str, str]] = dict(TIKTOK_MEDIA_HEADERS)

    @classmethod
    async def fetch(cls, url: str) -> MediaPost | None:
        normalized_url = parser.ensure_url_scheme(url)
        post_id, resolved_url = await cls._resolve_post_id(normalized_url)
        if not post_id:
            return None

        item_struct = await client.fetch_item_struct(post_id)
        if not item_struct:
            return None

        media_sources = await cls._extract_media_sources(item_struct)
        media = await cls._download_media(media_sources, post_id=post_id)
        if not media:
            return None

        author_name, author_handle = parser.extract_author(item_struct)
        text = parser.extract_text(item_struct)
        post_url = parser.build_post_url(item_struct, resolved_url or normalized_url)

        return MediaPost(
            author_name=author_name or author_handle or "TikTok",
            author_handle=author_handle or "tiktok",
            text=text,
            url=post_url,
            website=cls.website,
            media=media,
        )

    @classmethod
    async def _resolve_post_id(cls, url: str) -> tuple[str | None, str | None]:
        post_id = parser.extract_post_id(url)
        if post_id:
            return post_id, url

        resolved_url = await client.resolve_redirect_url(url)
        if not resolved_url:
            return None, None

        return parser.extract_post_id(resolved_url), resolved_url

    @classmethod
    async def _extract_media_sources(cls, item_struct: dict[str, object]) -> list[MediaSource]:
        sources = parser.extract_media_sources(item_struct)
        if not sources:
            return []

        if len(sources) == 1 and sources[0].kind == MediaKind.VIDEO:
            source = sources[0]
            resolved_url = await client.resolve_media_url(source.url)
            if resolved_url and resolved_url != source.url:
                return [
                    MediaSource(
                        kind=source.kind,
                        url=resolved_url,
                        thumbnail_url=source.thumbnail_url,
                        duration=source.duration,
                        width=source.width,
                        height=source.height,
                    )
                ]

        return sources

    @classmethod
    async def _download_media(cls, sources: list[MediaSource], *, post_id: str) -> list[MediaItem]:
        media = await cls.download_media(
            sources, filename_prefix="tiktok_media", max_size=TELEGRAM_MEDIA_MAX_FILE_SIZE_BYTES, log_label="TikTok"
        )
        if media:
            return media

        offload_sources = cls._build_offload_sources(post_id, sources)
        offload_media = await cls.download_media(
            offload_sources,
            filename_prefix="tiktok_media",
            max_size=TELEGRAM_MEDIA_MAX_FILE_SIZE_BYTES,
            log_label="TikTok Offload",
        )
        if offload_media:
            await logger.adebug(
                "[TikTok] Using downloaded offload fallback",
                source_count=len(offload_media),
                offload_url=_TNKTOK_OFFLOAD_BASE_URL,
            )
            return offload_media

        return []

    @classmethod
    def _build_offload_sources(cls, post_id: str, sources: list[MediaSource]) -> list[MediaSource]:
        base_url = _TNKTOK_OFFLOAD_BASE_URL
        photo_index = 1
        fallback_sources: list[MediaSource] = []

        for source in sources:
            if source.kind == MediaKind.VIDEO:
                offload_url = f"{base_url}/generate/video/{post_id}.mp4"
            else:
                offload_url = f"{base_url}/generate/image/{post_id}/{photo_index}"
                photo_index += 1

            fallback_sources.append(
                MediaSource(
                    kind=source.kind,
                    url=offload_url,
                    duration=source.duration,
                    width=source.width,
                    height=source.height,
                )
            )

        return fallback_sources
