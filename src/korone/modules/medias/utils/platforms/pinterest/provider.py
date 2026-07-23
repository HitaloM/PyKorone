import asyncio
import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from aiogram.types import BufferedInputFile

from korone.constants import TELEGRAM_MEDIA_MAX_FILE_SIZE_BYTES
from korone.logger import get_logger
from korone.modules.medias.utils.provider_base import MediaProvider
from korone.modules.medias.utils.types import MediaItem, MediaKind, MediaPost
from korone.modules.utils_.file_id_cache import get_cached_file_payload

from . import client, parser
from .constants import PATTERN, PINTEREST_HLS_TIMEOUT_SECONDS, PINTEREST_TIMEOUT

if TYPE_CHECKING:
    from aiogram.types import InputFile

    from korone.modules.medias.utils.types import MediaSource

logger = get_logger(__name__)


class PinterestProvider(MediaProvider):
    name = "Pinterest"
    website = "Pinterest"
    pattern = PATTERN
    _DEFAULT_TIMEOUT = PINTEREST_TIMEOUT
    _PAGE_HEADERS: ClassVar[dict[str, str]] = {
        **MediaProvider._DEFAULT_HEADERS,
        "Referer": "https://www.pinterest.com/",
    }

    @classmethod
    async def fetch(cls, url: str) -> MediaPost | None:
        post_id = parser.extract_post_id(url)
        if not post_id:
            resolved_url = await client.resolve_pin_url(
                url, headers=cls._PAGE_HEADERS, short_id=parser.extract_shortener_id(url)
            )
            if not resolved_url:
                return None

            post_id = parser.extract_post_id(resolved_url)
            if not post_id:
                return None

        html_content = await client.fetch_pin_page(post_id, headers=cls._PAGE_HEADERS)
        if not html_content:
            return None

        pin_data = parser.extract_pin_data(html_content)
        if not pin_data:
            await logger.adebug("[Pinterest] Relay pin data not found", post_id=post_id)
            return None

        sources = parser.extract_media_sources(pin_data)
        media = await cls.download_media(
            sources,
            filename_prefix="pinterest_media",
            max_size=TELEGRAM_MEDIA_MAX_FILE_SIZE_BYTES,
            log_label="Pinterest",
        )
        if not media:
            return None

        author_handle = parser.extract_author(pin_data)
        return MediaPost(
            author_name=author_handle or "Pinterest",
            author_handle=author_handle or "pinterest",
            text=parser.extract_text(pin_data),
            url=parser.build_post_url(post_id),
            website=cls.website,
            media=media,
        )

    @classmethod
    async def _download_source(
        cls, source: MediaSource, index: int, prefix: str, max_size: int | None, label: str
    ) -> MediaItem | None:
        if source.kind != MediaKind.VIDEO or not parser.is_hls_url(source.url):
            return await super()._download_source(source, index, prefix, max_size, label)

        cache_key = cls._media_source_cache_key(source.url)
        cached_payload = await get_cached_file_payload(cache_key)
        if cached_payload:
            cached_file_id = cached_payload.get("file_id")
            if isinstance(cached_file_id, str) and cached_file_id:
                return MediaItem(
                    kind=source.kind,
                    file=cached_file_id,
                    filename=f"{prefix}_{index}.mp4",
                    source_url=source.url,
                    duration=source.duration,
                    width=source.width,
                    height=source.height,
                )

        payload = await asyncio.to_thread(
            cls._download_hls_payload, source.url, cls._DEFAULT_HEADERS["User-Agent"], max_size
        )
        if payload is None:
            await logger.awarning("[Pinterest] Failed to remux HLS media", source_url=source.url, source_index=index)
            return None

        thumbnail: InputFile | None = None
        if source.thumbnail_url:
            thumbnail = await cls._download_thumbnail(source.thumbnail_url, label, index, prefix)

        filename = f"{prefix}_{index}.mp4"
        return MediaItem(
            kind=source.kind,
            file=BufferedInputFile(payload, filename),
            filename=filename,
            source_url=source.url,
            thumbnail=thumbnail,
            duration=source.duration,
            width=source.width,
            height=source.height,
        )

    @staticmethod
    def _download_hls_payload(url: str, user_agent: str, max_size: int | None) -> bytes | None:
        with tempfile.TemporaryDirectory(prefix="korone-pinterest-hls-") as temp_dir:
            output_path = Path(temp_dir) / "output.mp4"
            command = [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-user_agent",
                user_agent,
                "-i",
                url,
                "-c",
                "copy",
                "-movflags",
                "+faststart",
                str(output_path),
            ]

            try:
                result = subprocess.run(
                    command, capture_output=True, text=True, check=False, timeout=PINTEREST_HLS_TIMEOUT_SECONDS
                )
            except OSError, subprocess.TimeoutExpired:
                return None

            if result.returncode != 0 or not output_path.exists():
                return None

            if max_size is not None and output_path.stat().st_size > max_size:
                return None

            return output_path.read_bytes()
