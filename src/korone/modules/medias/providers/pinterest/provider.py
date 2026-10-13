from typing import TYPE_CHECKING

from aiogram.types import FSInputFile

from korone.logger import get_logger
from korone.modules.medias.download import DEFAULT_MEDIA_HEADERS, DownloadOptions, DownloadRequest
from korone.modules.medias.models import MediaKind, MediaPost, PreparedMedia, ProviderInfo

from . import parser
from .constants import PATTERN, PINTEREST_HLS_TIMEOUT_SECONDS, PINTEREST_TIMEOUT

if TYPE_CHECKING:
    from pathlib import Path

    from aiogram.types import InputFile

    from korone.modules.medias.download import MediaDownloader
    from korone.modules.medias.transforms import FFmpegTranscoder

    from .client import PinterestClient

logger = get_logger(__name__)


class PinterestProvider:
    info = ProviderInfo(key="pinterest", name="Pinterest", website="Pinterest", pattern=PATTERN)
    _PAGE_HEADERS = DEFAULT_MEDIA_HEADERS | {"Referer": "https://www.pinterest.com/"}

    def __init__(self, client: PinterestClient, downloader: MediaDownloader, transcoder: FFmpegTranscoder) -> None:
        self._client = client
        self._downloader = downloader
        self._transcoder = transcoder

    async def fetch(self, url: str, *, workspace: Path) -> MediaPost | None:
        post_id = parser.extract_post_id(url)
        if not post_id:
            resolved_url = await self._client.resolve_pin_url(
                url, headers=self._PAGE_HEADERS, short_id=parser.extract_shortener_id(url)
            )
            post_id = parser.extract_post_id(resolved_url) if resolved_url else None
        if not post_id:
            return None

        html_content = await self._client.fetch_pin_page(post_id, headers=self._PAGE_HEADERS)
        if not html_content or not (pin_data := parser.extract_pin_data(html_content)):
            if html_content:
                await logger.adebug("[Pinterest] Relay pin data not found", post_id=post_id)
            return None

        media = await self._downloader.download(
            parser.extract_media_sources(pin_data),
            options=DownloadOptions(
                workspace=workspace, filename_prefix="pinterest_media", label=self.info.name, timeout=PINTEREST_TIMEOUT
            ),
            loader=self._download_source,
        )
        if not media:
            return None

        author_handle = parser.extract_author(pin_data)
        return MediaPost(
            author_name=author_handle or "",
            author_handle=author_handle or "",
            text=parser.extract_text(pin_data),
            url=parser.build_post_url(post_id),
            website=self.info.website,
            media=media,
        )

    async def _download_source(self, request: DownloadRequest) -> PreparedMedia | None:
        source = request.source
        if source.kind != MediaKind.VIDEO or not parser.is_hls_url(source.url):
            return await self._downloader.download_source(request)

        output_path = await self._download_hls_file(request)
        if output_path is None:
            await logger.awarning(
                "[Pinterest] Failed to remux HLS media", source_url=source.url, source_index=request.index
            )
            return None

        thumbnail: InputFile | None = None
        if source.thumbnail_url:
            thumbnail = await self._downloader.download_thumbnail(source.thumbnail_url, request)
        filename = f"{request.options.filename_prefix}_{request.index}.mp4"
        return PreparedMedia(
            kind=source.kind,
            file=FSInputFile(output_path, filename),
            filename=filename,
            source_url=source.url,
            thumbnail=thumbnail,
            duration=source.duration,
            width=source.width,
            height=source.height,
        )

    async def _download_hls_file(self, request: DownloadRequest) -> Path | None:
        output_path = (
            self._downloader.source_directory(request) / f"{request.options.filename_prefix}_{request.index}.mp4"
        )
        max_size = self._downloader.size_limit(request)
        command = [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-user_agent",
            request.options.headers["User-Agent"],
            "-rw_timeout",
            "60000000",
            "-i",
            request.source.url,
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            # Leave one byte above the budget so a size-limited remux is rejected rather than delivered truncated.
            "-fs",
            str(max_size + 1),
            str(output_path),
        ]
        async with self._downloader.reserve_slot():
            return await self._transcoder.run_to_file(
                command,
                output_path,
                timeout_seconds=self._downloader.local_timeout_seconds or PINTEREST_HLS_TIMEOUT_SECONDS,
                max_size=max_size,
            )
