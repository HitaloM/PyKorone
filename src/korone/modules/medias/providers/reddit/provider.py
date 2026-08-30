import tempfile
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import quote, urljoin, urlparse, urlunparse

import aiohttp
from aiogram.types import BufferedInputFile
from lxml import html as lxml_html

from korone.constants import TELEGRAM_MEDIA_MAX_FILE_SIZE_BYTES
from korone.logger import get_logger
from korone.modules.medias.download import DEFAULT_MEDIA_HEADERS, DownloadOptions, DownloadRequest
from korone.modules.medias.models import MediaKind, MediaPost, MediaSource, PreparedMedia, ProviderInfo
from korone.modules.medias.parsing import coerce_int

from . import hls, parser
from .constants import (
    BLOCK_MARKERS,
    PATTERN,
    PLAYLIST_REGEX,
    REDDIT_HLS_REMUX_TIMEOUT_SECONDS,
    REDLIB_INSTANCES,
    REDLIB_REQUEST_COOKIES,
    VIDEO_REGEX,
)
from .models import _PostRef, _ScrapedPost

if TYPE_CHECKING:
    from aiogram.types import InputFile

    from korone.modules.medias.download import MediaDownloader
    from korone.modules.medias.transforms import FFmpegTranscoder

    from .client import RedditClient

logger = get_logger(__name__)


class RedditProvider:
    info = ProviderInfo(key="reddit", name="Reddit", website="Reddit", pattern=PATTERN, author_handle_prefix="")
    _TIMEOUT = aiohttp.ClientTimeout(total=90, connect=20, sock_read=60)
    _video_regex = VIDEO_REGEX
    _playlist_regex = PLAYLIST_REGEX

    def __init__(self, client: RedditClient, downloader: MediaDownloader, transcoder: FFmpegTranscoder) -> None:
        self._client = client
        self._downloader = downloader
        self._transcoder = transcoder

    async def fetch(self, url: str) -> MediaPost | None:
        post_ref = await self._resolve_post_ref(url)
        if not post_ref:
            return None

        html_payload = await self._fetch_redlib_payload(post_ref)
        if not html_payload:
            return None

        html_content = html_payload["html"]
        base_url = html_payload["base_url"]

        scraped = await self._scrape_post(html_content, base_url, post_ref)
        if not scraped or not scraped.media_sources:
            return None

        media = await self._downloader.download(
            scraped.media_sources,
            options=DownloadOptions(
                filename_prefix="reddit_media",
                label=self.info.name,
                max_size=TELEGRAM_MEDIA_MAX_FILE_SIZE_BYTES,
                timeout=self._TIMEOUT,
            ),
            loader=self._download_source,
        )
        if not media:
            return None

        return MediaPost(
            author_name=scraped.author or "",
            author_handle=scraped.subreddit or "",
            text=scraped.title,
            url=scraped.post_url,
            website=self.info.website,
            media=media,
        )

    async def _resolve_post_ref(self, url: str) -> _PostRef | None:
        post_ref = self._extract_post_ref(url)
        if post_ref or not parser.is_share_url(url):
            return post_ref

        resolved_url = await self._client.resolve_url(url, headers=DEFAULT_MEDIA_HEADERS, request_timeout=self._TIMEOUT)
        if resolved_url:
            if post_ref := self._extract_post_ref(resolved_url):
                return post_ref
            await logger.adebug(
                "[Reddit] Share URL did not resolve to a supported post", source_url=url, resolved_url=resolved_url
            )

        for redlib_url in self._redlib_share_urls(url):
            payload = await self._fetch_redlib_html(redlib_url)
            if payload and (post_ref := self._extract_post_ref_from_payload(payload)):
                return post_ref

        await logger.adebug("[Reddit] Could not resolve share URL", source_url=url)
        return None

    def _redlib_share_urls(self, url: str) -> list[str]:
        parsed_share_url = urlparse(parser.ensure_url_scheme(url))
        candidates: list[str] = []
        for instance in self._instance_candidates():
            parsed_instance = urlparse(instance)
            candidates.append(
                urlunparse(
                    parsed_instance._replace(
                        path=parsed_share_url.path,
                        params=parsed_share_url.params,
                        query=parsed_share_url.query,
                        fragment="",
                    )
                )
            )
        return list(dict.fromkeys(candidates))

    def _extract_post_ref_from_payload(self, payload: dict[str, str]) -> _PostRef | None:
        base_url = payload.get("base_url", "")
        candidates = [base_url]
        try:
            tree = lxml_html.fromstring(payload.get("html", ""))
        except ValueError, TypeError:
            tree = None

        if tree is not None:
            for xpath in (
                "//p[@id='reddit_url']/text()",
                "//meta[@property='og:url']/@content",
                "//meta[@property='twitter:url']/@content",
                "//link[@rel='canonical']/@href",
            ):
                candidates.extend(value for value in tree.xpath(xpath) if isinstance(value, str))

        for candidate in candidates:
            if post_ref := self._extract_post_ref(urljoin(base_url, candidate)):
                return post_ref
        return None

    @staticmethod
    def _extract_post_ref(url: str) -> _PostRef | None:
        normalized_url = parser.ensure_url_scheme(url)
        parsed = urlparse(normalized_url)
        host = parsed.netloc.lower()
        segments = [segment for segment in parsed.path.split("/") if segment]
        if not segments:
            return None

        if host.endswith("redd.it"):
            short_id = parser.normalize_post_id(segments[0])
            if not short_id:
                return None
            return _PostRef(kind="comments", name=None, post_id=short_id)

        for index, segment in enumerate(segments):
            if segment.lower() != "comments" or index + 1 >= len(segments):
                continue

            post_id = parser.normalize_post_id(segments[index + 1])
            if not post_id:
                continue

            if index >= 2:
                kind = segments[index - 2].lower()
                name = segments[index - 1]
                if kind in {"r", "user"} and name:
                    return _PostRef(kind=kind, name=name, post_id=post_id)

            return _PostRef(kind="comments", name=None, post_id=post_id)

        return None

    @staticmethod
    def _instance_candidates() -> list[str]:
        candidates = [candidate.rstrip("/") for candidate in REDLIB_INSTANCES]
        return [candidate for candidate in dict.fromkeys(candidates) if candidate]

    @staticmethod
    def _build_redlib_url(post_ref: _PostRef, instance: str) -> str:
        instance_base = instance.rstrip("/")
        if post_ref.kind in {"r", "user"} and post_ref.name:
            return f"{instance_base}/{post_ref.kind}/{quote(post_ref.name)}/comments/{quote(post_ref.post_id)}"
        return f"{instance_base}/comments/{quote(post_ref.post_id)}"

    async def _fetch_redlib_payload(self, post_ref: _PostRef) -> dict[str, str] | None:
        for instance in self._instance_candidates():
            redlib_url = self._build_redlib_url(post_ref, instance)
            payload = await self._fetch_redlib_html(redlib_url)
            if not payload:
                continue

            html_content = payload.get("html", "")
            if parser.looks_like_block_page(html_content, BLOCK_MARKERS):
                await logger.adebug("[Reddit] Redlib blocked request", url=redlib_url)
                continue

            base_url = payload.get("base_url") or redlib_url
            return {"html": html_content, "base_url": base_url}

        return None

    async def _fetch_redlib_html(self, redlib_url: str) -> dict[str, str] | None:
        payload: dict[str, str] | None = None
        try:
            payload = await self._client.request_page(
                redlib_url, headers=DEFAULT_MEDIA_HEADERS, cookies=REDLIB_REQUEST_COOKIES, request_timeout=self._TIMEOUT
            )
            if not payload:
                await logger.adebug("[Reddit] Non-200 Redlib response", url=redlib_url)
                return None

            html_content = payload.get("html", "")
            if not parser.looks_like_block_page(html_content, BLOCK_MARKERS):
                return payload

            solved_payload = await self._client.solve_anubis(
                challenge_html=html_content,
                challenge_url=payload.get("base_url") or redlib_url,
                headers=DEFAULT_MEDIA_HEADERS,
                request_timeout=self._TIMEOUT,
            )
            if solved_payload:
                return solved_payload
        except TimeoutError:
            await logger.awarning("[Reddit] Timeout while fetching Redlib page", url=redlib_url)
            return None
        except aiohttp.ClientError as exc:
            await logger.awarning("[Reddit] Failed to fetch Redlib page", error=str(exc), url=redlib_url)
            return None
        return payload

    async def _scrape_post(self, html_content: str, base_url: str, post_ref: _PostRef) -> _ScrapedPost | None:
        try:
            tree = lxml_html.fromstring(html_content)
        except ValueError, TypeError:
            return None

        post_type = parser.extract_post_type(html_content)
        author = parser.extract_node_text(tree, "//a[contains(@class, 'post_author')]")
        subreddit = parser.extract_node_text(tree, "//a[contains(@class, 'post_subreddit')]")
        title = parser.extract_title(tree)
        post_url = self._extract_post_url(tree, post_ref)

        sources = await self._extract_media_sources(tree, html_content, base_url, post_type)
        if not sources:
            return None

        return _ScrapedPost(author=author, subreddit=subreddit, title=title, post_url=post_url, media_sources=sources)

    def _extract_post_url(self, tree: lxml_html.HtmlElement, post_ref: _PostRef) -> str:
        reddit_urls = tree.xpath("//p[@id='reddit_url']/text()")
        for raw_url in reddit_urls:
            if isinstance(raw_url, str) and raw_url.strip():
                return raw_url.strip()
        return self._build_fallback_reddit_url(post_ref)

    @staticmethod
    def _build_fallback_reddit_url(post_ref: _PostRef) -> str:
        if post_ref.kind in {"r", "user"} and post_ref.name:
            return f"https://www.reddit.com/{post_ref.kind}/{quote(post_ref.name)}/comments/{quote(post_ref.post_id)}"
        return f"https://www.reddit.com/comments/{quote(post_ref.post_id)}"

    async def _extract_media_sources(
        self, tree: lxml_html.HtmlElement, html_content: str, base_url: str, post_type: str
    ) -> list[MediaSource]:
        preferred = await self._extract_preferred_sources(tree, html_content, base_url, post_type)
        sources = self._normalize_sources(preferred, base_url)
        if not sources:
            sources = self._normalize_sources(self._gallery_sources(tree), base_url)
        if not sources:
            sources = self._normalize_sources(self._image_sources(tree), base_url)
        if not sources and (video := await self._extract_video_source(tree, html_content, base_url)):
            sources = self._normalize_sources([video], base_url)
        return sources

    async def _extract_preferred_sources(
        self, tree: lxml_html.HtmlElement, html_content: str, base_url: str, post_type: str
    ) -> list[MediaSource]:
        match post_type:
            case "gallery":
                return self._gallery_sources(tree)
            case "image":
                return self._image_sources(tree)
            case "video" | "gif":
                video = await self._extract_video_source(tree, html_content, base_url)
                return [video] if video else []
            case _:
                return []

    @staticmethod
    def _gallery_sources(tree: lxml_html.HtmlElement) -> list[MediaSource]:
        return [MediaSource(kind=MediaKind.PHOTO, url=url) for url in parser.extract_gallery_urls(tree)]

    @staticmethod
    def _image_sources(tree: lxml_html.HtmlElement) -> list[MediaSource]:
        image_url = parser.extract_image_url(tree)
        return [MediaSource(kind=MediaKind.PHOTO, url=image_url)] if image_url else []

    @staticmethod
    def _normalize_sources(sources: list[MediaSource], base_url: str) -> list[MediaSource]:
        normalized_sources: list[MediaSource] = []
        seen: set[str] = set()

        for source in sources:
            normalized_url = parser.normalize_media_url(base_url, source.url)
            if not normalized_url or normalized_url in seen:
                continue

            seen.add(normalized_url)
            normalized_thumb = (
                parser.normalize_media_url(base_url, source.thumbnail_url) if source.thumbnail_url else None
            )
            normalized_sources.append(
                MediaSource(
                    kind=source.kind,
                    url=normalized_url,
                    thumbnail_url=normalized_thumb,
                    duration=source.duration,
                    width=source.width,
                    height=source.height,
                    audio_url=source.audio_url,
                    fallback_url=source.fallback_url,
                )
            )
        return normalized_sources

    async def _extract_video_source(
        self, tree: lxml_html.HtmlElement, html_content: str, base_url: str
    ) -> MediaSource | None:
        video_nodes = tree.xpath(
            "//div[contains(@class, 'post_media_content')]//video[contains(@class, 'post_media_video')]"
        )
        if video_nodes and (source := await self._extract_video_node_source(video_nodes[0], base_url)):
            return source
        return await self._extract_embedded_video_source(html_content, base_url)

    async def _extract_video_node_source(self, video_node: lxml_html.HtmlElement, base_url: str) -> MediaSource | None:
        poster = video_node.get("poster")
        width = coerce_int(video_node.get("width"))
        height = coerce_int(video_node.get("height"))
        duration = parser.extract_video_duration_seconds(video_node)
        direct_mp4_url = self._extract_direct_mp4_url(video_node, base_url)
        hls_source = parser.first_non_empty(
            video_node.xpath(
                ".//source[@type='application/vnd.apple.mpegurl' "
                "or starts-with(@type, 'application/vnd.apple.mpegurl')]/@src"
            )
        )
        if hls_source and (
            resolved := await hls.resolve_streams(parser.normalize_media_url(base_url, hls_source), self._fetch_text)
        ):
            return MediaSource(
                kind=MediaKind.VIDEO,
                url=resolved.url,
                audio_url=resolved.audio_url,
                fallback_url=direct_mp4_url,
                thumbnail_url=poster,
                width=resolved.width or width,
                height=resolved.height or height,
                duration=resolved.duration or duration,
            )
        if not direct_mp4_url:
            return None
        return MediaSource(
            kind=MediaKind.VIDEO,
            url=direct_mp4_url,
            thumbnail_url=poster,
            width=width,
            height=height,
            duration=duration,
        )

    @staticmethod
    def _extract_direct_mp4_url(video_node: lxml_html.HtmlElement, base_url: str) -> str | None:
        candidates = [video_node.get("src") or ""]
        candidates.extend(
            str(source)
            for source in video_node.xpath(".//source[@type='video/mp4' or starts-with(@type, 'video/mp4')]/@src")
        )
        return next(
            (normalized for source in candidates if (normalized := parser.normalize_media_url(base_url, source))), None
        )

    async def _extract_embedded_video_source(self, html_content: str, base_url: str) -> MediaSource | None:
        mp4_match = self._video_regex.search(html_content)
        playlist_match = self._playlist_regex.search(html_content)
        if playlist_match and playlist_match.group(1):
            resolved = await hls.resolve_streams(
                parser.normalize_media_url(base_url, playlist_match.group(1)), self._fetch_text
            )
            if resolved:
                return MediaSource(
                    kind=MediaKind.VIDEO,
                    url=resolved.url,
                    audio_url=resolved.audio_url,
                    width=resolved.width,
                    height=resolved.height,
                    duration=resolved.duration,
                )

        if mp4_match and mp4_match.group(1):
            normalized = parser.normalize_media_url(base_url, mp4_match.group(1))
            if normalized:
                return MediaSource(kind=MediaKind.VIDEO, url=normalized)
        return None

    async def _fetch_text(self, url: str) -> str | None:
        try:
            text = await self._client.fetch_text(
                url, headers=DEFAULT_MEDIA_HEADERS, cookies=REDLIB_REQUEST_COOKIES, request_timeout=self._TIMEOUT
            )
        except TimeoutError:
            await logger.awarning("[Reddit] Playlist request timed out", url=url)
            return None
        except aiohttp.ClientError as exc:
            await logger.awarning("[Reddit] Playlist request failed", error=str(exc), url=url)
            return None

        if text is None:
            await logger.adebug("[Reddit] Failed to fetch playlist", url=url)
            return None

        return text

    async def _download_source(self, request: DownloadRequest) -> PreparedMedia | None:
        source = request.source
        if not source.audio_url:
            return await self._downloader.download_source(request)

        remuxed_payload = await self._download_and_remux_hls(request)
        if not remuxed_payload:
            await logger.awarning(
                "[Reddit] Failed to remux HLS media",
                source_url=source.url,
                audio_url=source.audio_url,
                source_index=request.index,
            )
            return await self._download_fallback_source(request)

        if request.options.max_size and len(remuxed_payload) > request.options.max_size:
            await logger.adebug(
                "[Reddit] Remuxed HLS media too large", size=len(remuxed_payload), source_url=source.url
            )
            return await self._download_fallback_source(request)

        thumbnail: InputFile | None = None
        if source.thumbnail_url and source.kind == MediaKind.VIDEO:
            thumbnail = await self._downloader.download_thumbnail(source.thumbnail_url, request)

        filename = f"{request.options.filename_prefix}_{request.index}.mp4"
        return PreparedMedia(
            kind=source.kind,
            file=BufferedInputFile(remuxed_payload, filename),
            filename=filename,
            source_url=source.url,
            thumbnail=thumbnail,
            duration=source.duration,
            width=source.width,
            height=source.height,
        )

    async def _download_fallback_source(self, request: DownloadRequest) -> PreparedMedia | None:
        source = request.source
        if not source.fallback_url:
            return None

        fallback_source = MediaSource(
            kind=source.kind,
            url=source.fallback_url,
            thumbnail_url=source.thumbnail_url,
            duration=source.duration,
            width=source.width,
            height=source.height,
        )
        fallback_request = replace(request, source=fallback_source)
        if cached_item := await self._downloader.get_cached_media(fallback_request):
            return cached_item
        return await self._downloader.download_source(fallback_request)

    async def _download_and_remux_hls(self, request: DownloadRequest) -> bytes | None:
        source = request.source
        with tempfile.TemporaryDirectory(prefix="korone-reddit-hls-") as temp_dir:
            temp_dir_path = Path(temp_dir)
            video_input_path = temp_dir_path / "video.ts"
            video_size = await self._downloader.fetch_to_path(
                source.url, request, video_input_path, max_size=request.options.max_size
            )
            if video_size is None:
                return None

            command = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(video_input_path)]
            if source.audio_url:
                remaining_size = None if request.options.max_size is None else request.options.max_size - video_size
                if remaining_size is not None and remaining_size <= 0:
                    return None
                audio_input_path = temp_dir_path / "audio.aac"
                audio_size = await self._downloader.fetch_to_path(
                    source.audio_url, request, audio_input_path, max_size=remaining_size
                )
                if audio_size is None:
                    await logger.awarning(
                        "[Reddit] Failed to fetch HLS audio payload",
                        source_url=source.audio_url,
                        video_url=source.url,
                        source_index=request.index,
                    )
                    return None
                command.extend(["-i", str(audio_input_path)])

            output_path = temp_dir_path / "output.mp4"
            command.extend(["-c", "copy", "-movflags", "+faststart"])
            if request.options.max_size is not None:
                command.extend(["-fs", str(request.options.max_size)])
            command.append(str(output_path))
            return await self._transcoder.run_to_payload(
                command,
                output_path,
                timeout_seconds=REDDIT_HLS_REMUX_TIMEOUT_SECONDS,
                max_size=request.options.max_size,
            )
