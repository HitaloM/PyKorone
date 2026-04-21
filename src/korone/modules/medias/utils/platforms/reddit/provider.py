from __future__ import annotations

import asyncio
import re
import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import quote, urljoin, urlparse, urlunparse

import aiohttp
from aiogram.types import BufferedInputFile
from lxml import html as lxml_html

from korone.constants import TELEGRAM_MEDIA_MAX_FILE_SIZE_BYTES
from korone.logger import get_logger
from korone.modules.medias.utils.parsing import coerce_int
from korone.modules.medias.utils.provider_base import MediaProvider
from korone.modules.medias.utils.types import MediaItem, MediaKind, MediaPost, MediaSource
from korone.modules.utils_.file_id_cache import get_cached_file_payload
from korone.utils.aiohttp_session import HTTPClient

from . import client, parser
from .anubis import RedlibAnubisBypassMixin
from .constants import (
    BLOCK_MARKERS,
    JSON_SCRIPT_REGEX_TEMPLATE,
    META_REFRESH_REGEX,
    PATTERN,
    PLAYLIST_REGEX,
    POST_TYPE_REGEX,
    REDLIB_INSTANCES,
    REDLIB_REQUEST_COOKIES,
    VIDEO_REGEX,
)
from .types import _PostRef, _ScrapedPost

if TYPE_CHECKING:
    from aiogram.types import InputFile

logger = get_logger(__name__)


class RedditProvider(RedlibAnubisBypassMixin, MediaProvider):
    name = "Reddit"
    website = "Reddit"
    _DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=90, connect=20, sock_read=60)

    pattern = PATTERN
    _post_type_regex = POST_TYPE_REGEX
    _video_regex = VIDEO_REGEX
    _playlist_regex = PLAYLIST_REGEX
    _json_script_regex_template = JSON_SCRIPT_REGEX_TEMPLATE
    _meta_refresh_regex = META_REFRESH_REGEX
    _block_markers = BLOCK_MARKERS

    @classmethod
    async def fetch(cls, url: str) -> MediaPost | None:
        post_ref = cls._extract_post_ref(url)
        if not post_ref:
            return None

        html_payload = await cls._fetch_redlib_payload(post_ref)
        if not html_payload:
            return None

        html_content = html_payload["html"]
        base_url = html_payload["base_url"]

        scraped = await cls._scrape_post(html_content, base_url, post_ref)
        if not scraped or not scraped.media_sources:
            return None

        media = await cls._download_media(scraped.media_sources)
        if not media:
            return None

        return MediaPost(
            author_name=scraped.author or "Reddit",
            author_handle=scraped.subreddit or "reddit",
            text=scraped.title,
            url=scraped.post_url,
            website=cls.website,
            media=media,
        )

    @classmethod
    def _extract_post_ref(cls, url: str) -> _PostRef | None:
        normalized_url = cls._ensure_url_scheme(url)
        parsed = urlparse(normalized_url)
        host = parsed.netloc.lower()
        segments = [segment for segment in parsed.path.split("/") if segment]
        if not segments:
            return None

        if host.endswith("redd.it"):
            short_id = cls._normalize_post_id(segments[0])
            if not short_id:
                return None
            return _PostRef(kind="comments", name=None, post_id=short_id)

        for index, segment in enumerate(segments):
            if segment.lower() != "comments" or index + 1 >= len(segments):
                continue

            post_id = cls._normalize_post_id(segments[index + 1])
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
    def _normalize_post_id(post_id: str) -> str | None:
        return parser.normalize_post_id(post_id)

    @staticmethod
    def _ensure_url_scheme(url: str) -> str:
        return parser.ensure_url_scheme(url)

    @classmethod
    def _instance_candidates(cls) -> list[str]:
        candidates = [candidate.rstrip("/") for candidate in REDLIB_INSTANCES]
        return [candidate for candidate in dict.fromkeys(candidates) if candidate]

    @classmethod
    def _build_redlib_url(cls, post_ref: _PostRef, instance: str) -> str:
        instance_base = instance.rstrip("/")
        if post_ref.kind in {"r", "user"} and post_ref.name:
            return f"{instance_base}/{post_ref.kind}/{quote(post_ref.name)}/comments/{quote(post_ref.post_id)}"
        return f"{instance_base}/comments/{quote(post_ref.post_id)}"

    @classmethod
    async def _fetch_redlib_payload(cls, post_ref: _PostRef) -> dict[str, str] | None:
        for instance in cls._instance_candidates():
            redlib_url = cls._build_redlib_url(post_ref, instance)
            payload = await cls._fetch_redlib_html(redlib_url)
            if not payload:
                continue

            html_content = payload.get("html", "")
            if cls._looks_like_block_page(html_content):
                await logger.adebug("[Reddit] Redlib blocked request", url=redlib_url)
                continue

            base_url = payload.get("base_url") or redlib_url
            return {"html": html_content, "base_url": base_url}

        return None

    @classmethod
    async def _fetch_redlib_html(cls, redlib_url: str) -> dict[str, str] | None:
        payload: dict[str, str] | None = None
        try:
            session = await HTTPClient.get_session()
            payload = await cls._request_redlib_page(session, redlib_url, headers=cls._DEFAULT_HEADERS)
            if not payload:
                return None

            html_content = payload.get("html", "")
            if not cls._looks_like_block_page(html_content):
                return payload

            solved_payload = await cls._solve_anubis_challenge(
                session,
                challenge_html=html_content,
                challenge_url=payload.get("base_url") or redlib_url,
                headers=cls._DEFAULT_HEADERS,
            )
            if solved_payload:
                return solved_payload
        except TimeoutError:
            await logger.awarning("[Reddit] Timeout while fetching Redlib page", url=redlib_url)
            return None
        except aiohttp.ClientError as exc:
            await logger.aerror("[Reddit] Failed to fetch Redlib page", error=str(exc), url=redlib_url)
            return None
        return payload

    @classmethod
    async def _request_redlib_page(
        cls, session: aiohttp.ClientSession, url: str, *, headers: dict[str, str]
    ) -> dict[str, str] | None:
        payload = await client.request_redlib_page(
            url, headers=headers, cookies=REDLIB_REQUEST_COOKIES, request_timeout=cls._DEFAULT_TIMEOUT
        )
        if not payload:
            await logger.adebug("[Reddit] Non-200 Redlib response", url=url)
            return None
        return payload

    @classmethod
    def _looks_like_block_page(cls, html_content: str) -> bool:
        return parser.looks_like_block_page(html_content, cls._block_markers)

    @classmethod
    async def _scrape_post(cls, html_content: str, base_url: str, post_ref: _PostRef) -> _ScrapedPost | None:
        try:
            tree = lxml_html.fromstring(html_content)
        except ValueError, TypeError:
            return None

        post_type = cls._extract_post_type(html_content)
        author = cls._extract_node_text(tree, "//a[contains(@class, 'post_author')]")
        subreddit = cls._extract_node_text(tree, "//a[contains(@class, 'post_subreddit')]")
        title = cls._extract_title(tree)
        post_url = cls._extract_post_url(tree, post_ref)

        sources = await cls._extract_media_sources(tree, html_content, base_url, post_type)
        if not sources:
            return None

        return _ScrapedPost(author=author, subreddit=subreddit, title=title, post_url=post_url, media_sources=sources)

    @classmethod
    def _extract_post_type(cls, html_content: str) -> str:
        match = cls._post_type_regex.search(html_content)
        if match:
            return match.group(1).strip().lower()
        return ""

    @classmethod
    def _extract_node_text(cls, tree: lxml_html.HtmlElement, xpath: str) -> str:
        node = tree.xpath(xpath)
        if not node:
            return ""
        first = node[0]
        text = first.text_content() if hasattr(first, "text_content") else str(first)
        return " ".join(text.split()).strip()

    @classmethod
    def _extract_title(cls, tree: lxml_html.HtmlElement) -> str:
        title_parts = tree.xpath("//h1[contains(@class, 'post_title')]/text()")
        cleaned = [part.strip() for part in title_parts if isinstance(part, str) and part.strip()]
        return " ".join(cleaned)

    @classmethod
    def _extract_post_url(cls, tree: lxml_html.HtmlElement, post_ref: _PostRef) -> str:
        reddit_urls = tree.xpath("//p[@id='reddit_url']/text()")
        for raw_url in reddit_urls:
            if isinstance(raw_url, str) and raw_url.strip():
                return raw_url.strip()
        return cls._build_fallback_reddit_url(post_ref)

    @staticmethod
    def _build_fallback_reddit_url(post_ref: _PostRef) -> str:
        if post_ref.kind in {"r", "user"} and post_ref.name:
            return f"https://www.reddit.com/{post_ref.kind}/{quote(post_ref.name)}/comments/{quote(post_ref.post_id)}"
        return f"https://www.reddit.com/comments/{quote(post_ref.post_id)}"

    @classmethod
    async def _extract_media_sources(
        cls, tree: lxml_html.HtmlElement, html_content: str, base_url: str, post_type: str
    ) -> list[MediaSource]:
        sources: list[MediaSource] = []
        seen: set[str] = set()

        def add_source(source: MediaSource) -> None:
            if not source.url:
                return
            normalized_url = parser.normalize_media_url(base_url, source.url)
            if not normalized_url or normalized_url in seen:
                return

            seen.add(normalized_url)
            normalized_thumb = (
                parser.normalize_media_url(base_url, source.thumbnail_url) if source.thumbnail_url else None
            )
            sources.append(
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

        if post_type == "gallery":
            for gallery_url in cls._extract_gallery_urls(tree):
                add_source(MediaSource(kind=MediaKind.PHOTO, url=gallery_url))

        if post_type == "image" and not sources:
            image_url = cls._extract_image_url(tree)
            add_source(MediaSource(kind=MediaKind.PHOTO, url=image_url or ""))

        if post_type in {"video", "gif"} and not sources:
            video = await cls._extract_video_source(tree, html_content, base_url)
            if video:
                add_source(video)

        if not sources:
            for gallery_url in cls._extract_gallery_urls(tree):
                add_source(MediaSource(kind=MediaKind.PHOTO, url=gallery_url))

        if not sources:
            image_url = cls._extract_image_url(tree)
            add_source(MediaSource(kind=MediaKind.PHOTO, url=image_url or ""))

        if not sources:
            video = await cls._extract_video_source(tree, html_content, base_url)
            if video:
                add_source(video)

        return sources

    @classmethod
    def _extract_gallery_urls(cls, tree: lxml_html.HtmlElement) -> list[str]:
        urls: list[str] = []
        gallery_nodes = tree.xpath("//div[contains(@class, 'gallery')]//figure")
        for figure in gallery_nodes:
            href = parser.first_non_empty(figure.xpath(".//a/@href"))
            src = parser.first_non_empty(figure.xpath(".//img[@alt='Gallery image']/@src"))
            selected = href or src
            if selected:
                urls.append(selected)
        return urls

    @classmethod
    def _extract_image_url(cls, tree: lxml_html.HtmlElement) -> str | None:
        return (
            parser.first_non_empty(
                tree.xpath(
                    "//div[contains(@class, 'post_media_content')]//a[contains(@class, 'post_media_image')]/@href"
                )
            )
            or parser.first_non_empty(tree.xpath("//div[contains(@class, 'post_media_content')]//img/@src"))
            or parser.first_non_empty(tree.xpath("//meta[@property='og:image']/@content"))
        )

    @classmethod
    async def _extract_video_source(
        cls, tree: lxml_html.HtmlElement, html_content: str, base_url: str
    ) -> MediaSource | None:
        video_nodes = tree.xpath(
            "//div[contains(@class, 'post_media_content')]//video[contains(@class, 'post_media_video')]"
        )
        if video_nodes:
            video_node = video_nodes[0]
            poster = video_node.get("poster")
            width = coerce_int(video_node.get("width"))
            height = coerce_int(video_node.get("height"))
            duration = cls._extract_video_duration_seconds(video_node)

            direct_mp4_url = None
            direct_mp4_sources = [video_node.get("src") or ""]
            direct_mp4_sources.extend(
                str(source)
                for source in video_node.xpath(".//source[@type='video/mp4' or starts-with(@type, 'video/mp4')]/@src")
            )
            for source in direct_mp4_sources:
                normalized = parser.normalize_media_url(base_url, source)
                if normalized:
                    direct_mp4_url = normalized
                    break

            hls_source = parser.first_non_empty(
                video_node.xpath(
                    ".//source[@type='application/vnd.apple.mpegurl' "
                    "or starts-with(@type, 'application/vnd.apple.mpegurl')]/@src"
                )
            )
            if hls_source:
                resolved = await cls._resolve_hls_streams(parser.normalize_media_url(base_url, hls_source))
                if resolved:
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

            if direct_mp4_url:
                return MediaSource(
                    kind=MediaKind.VIDEO,
                    url=direct_mp4_url,
                    thumbnail_url=poster,
                    width=width,
                    height=height,
                    duration=duration,
                )

        mp4_match = cls._video_regex.search(html_content)
        playlist_match = cls._playlist_regex.search(html_content)
        if playlist_match and playlist_match.group(1):
            resolved = await cls._resolve_hls_streams(parser.normalize_media_url(base_url, playlist_match.group(1)))
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

    @classmethod
    async def _resolve_hls_streams(cls, hls_url: str | None) -> MediaSource | None:
        if not hls_url:
            return None

        master_playlist = await cls._fetch_text(hls_url)
        if not master_playlist:
            return None

        audio_groups: dict[str, str] = {}
        best_variant: str | None = None
        best_bandwidth = -1
        best_width: int | None = None
        best_height: int | None = None
        best_audio_group: str | None = None

        stream_info: str | None = None
        for raw_line in master_playlist.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("#EXT-X-MEDIA:"):
                media_type = cls._parse_stream_text(line, "TYPE")
                group_id = cls._parse_stream_text(line, "GROUP-ID")
                uri = cls._parse_stream_text(line, "URI")
                if media_type == "AUDIO" and group_id and uri:
                    audio_groups[group_id] = uri
                continue
            if line.startswith("#EXT-X-STREAM-INF:"):
                stream_info = line
                continue
            if line.startswith("#"):
                continue
            if stream_info is None:
                continue

            bandwidth = cls._parse_stream_int(stream_info, "BANDWIDTH")
            width, height = cls._parse_stream_resolution(stream_info)
            audio_group = cls._parse_stream_text(stream_info, "AUDIO")
            if bandwidth > best_bandwidth:
                best_bandwidth = bandwidth
                best_variant = line
                best_width = width
                best_height = height
                best_audio_group = audio_group

            if best_variant is None:
                best_variant = line
                best_width = width
                best_height = height
                best_audio_group = audio_group

            stream_info = None

        if not best_variant:
            return None

        variant_playlist_url = parser.normalize_media_url(hls_url, best_variant)
        if not variant_playlist_url:
            return None

        variant_playlist = await cls._fetch_text(variant_playlist_url)
        if not variant_playlist:
            return None

        video_path = cls._extract_playlist_media_path(variant_playlist)
        if not video_path:
            return None

        video_url = parser.normalize_media_url(variant_playlist_url, video_path)
        if not video_url:
            return None

        audio_url: str | None = None
        audio_uri_candidates: list[str] = []
        if best_audio_group:
            candidate = audio_groups.get(best_audio_group)
            if candidate:
                audio_uri_candidates.append(candidate)
        audio_uri_candidates.extend(uri for uri in audio_groups.values() if uri not in audio_uri_candidates)

        for audio_uri in audio_uri_candidates:
            audio_playlist_url = parser.normalize_media_url(hls_url, audio_uri)
            if not audio_playlist_url:
                continue

            audio_playlist = await cls._fetch_text(audio_playlist_url)
            if not audio_playlist:
                continue

            audio_path = cls._extract_playlist_media_path(audio_playlist)
            if not audio_path:
                continue

            audio_url = parser.normalize_media_url(audio_playlist_url, audio_path)
            if audio_url:
                break

        variant_duration = cls._parse_hls_segment_duration(variant_playlist)

        return MediaSource(
            kind=MediaKind.VIDEO,
            url=video_url,
            audio_url=audio_url,
            width=best_width,
            height=best_height,
            duration=variant_duration,
        )

    @staticmethod
    def _extract_playlist_media_path(playlist: str) -> str | None:
        for raw_line in playlist.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            return line
        return None

    @staticmethod
    def _parse_stream_text(stream_info: str, key: str) -> str | None:
        match = re.search(rf'{re.escape(key)}=(?:"([^"]*)"|([^,\s]+))', stream_info)
        if not match:
            return None
        return match.group(1) or match.group(2)

    @classmethod
    def _extract_video_duration_seconds(cls, video_node: lxml_html.HtmlElement) -> int | None:
        duration_candidates = (
            video_node.get("duration"),
            video_node.get("data-duration"),
            video_node.get("data-video-duration"),
            video_node.get("data-length"),
            video_node.get("data-video-length"),
        )
        for raw_duration in duration_candidates:
            duration = coerce_int(raw_duration)
            if duration and duration > 0:
                return duration

            if isinstance(raw_duration, str):
                clock_duration = cls._parse_clock_duration_seconds(raw_duration)
                if clock_duration is not None:
                    return clock_duration

        return None

    @staticmethod
    def _parse_clock_duration_seconds(raw_duration: str) -> int | None:
        normalized = raw_duration.strip()
        if ":" not in normalized:
            return None

        parts = normalized.split(":")
        if len(parts) not in {2, 3}:
            return None
        if any(not part.isdigit() for part in parts):
            return None

        total = 0
        for part in parts:
            total = (total * 60) + int(part)
        return total if total > 0 else None

    @classmethod
    async def _extract_hls_duration_seconds(cls, hls_variant_url: str) -> int | None:
        parsed_variant = urlparse(hls_variant_url)
        if not parsed_variant.path.endswith(".m3u8"):
            return None

        playlist = await cls._fetch_text(hls_variant_url)
        if not playlist:
            return None

        return cls._parse_hls_segment_duration(playlist)

    @staticmethod
    def _parse_hls_segment_duration(playlist: str) -> int | None:
        total_seconds = 0.0
        has_segments = False

        for raw_line in playlist.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            match = re.match(r"(?i)#EXTINF:([0-9]+(?:\.[0-9]+)?)", line)
            if not match:
                continue

            try:
                segment_duration = float(match.group(1))
            except ValueError:
                continue

            if segment_duration <= 0:
                continue

            has_segments = True
            total_seconds += segment_duration

        if not has_segments:
            return None

        rounded_duration = int(total_seconds + 0.5)
        return rounded_duration if rounded_duration > 0 else 1

    @classmethod
    async def _fetch_text(cls, url: str) -> str | None:
        try:
            text = await client.fetch_text(
                url, headers=cls._DEFAULT_HEADERS, cookies=REDLIB_REQUEST_COOKIES, request_timeout=cls._DEFAULT_TIMEOUT
            )
        except TimeoutError:
            await logger.awarning("[Reddit] Playlist request timed out", url=url)
            return None
        except aiohttp.ClientError as exc:
            await logger.aerror("[Reddit] Playlist request failed", error=str(exc), url=url)
            return None

        if text is None:
            await logger.adebug("[Reddit] Failed to fetch playlist", url=url)
            return None

        return text

    @classmethod
    def _join_hls_url(cls, master_url: str, playlist_path: str) -> str:
        joined = urljoin(master_url, playlist_path)
        master = urlparse(master_url)
        parsed_joined = urlparse(joined)
        if parsed_joined.query:
            return joined
        return urlunparse(parsed_joined._replace(query=master.query))

    @staticmethod
    def _parse_stream_int(stream_info: str, key: str) -> int:
        match = re.search(rf"{re.escape(key)}=(\d+)", stream_info)
        if not match:
            return -1
        try:
            return int(match.group(1))
        except ValueError:
            return -1

    @staticmethod
    def _parse_stream_resolution(stream_info: str) -> tuple[int | None, int | None]:
        match = re.search(r"RESOLUTION=(\d+)x(\d+)", stream_info)
        if not match:
            return None, None
        try:
            return int(match.group(1)), int(match.group(2))
        except ValueError:
            return None, None

    @classmethod
    async def _download_source(
        cls, source: MediaSource, index: int, prefix: str, max_size: int | None, label: str
    ) -> MediaItem | None:
        if not source.audio_url:
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

        video_payload_result = await cls._fetch_payload_with_retry(
            source.url, label=label, stage="source", max_size=max_size, source_kind=source.kind, source_index=index
        )
        if not video_payload_result:
            return await cls._download_fallback_source(source, index, prefix, max_size, label)

        video_payload, _ = video_payload_result

        audio_payload: bytes | None = None
        if source.audio_url:
            audio_payload_result = await cls._fetch_payload_with_retry(
                source.audio_url,
                label=label,
                stage="source",
                max_size=max_size,
                source_kind=source.kind,
                source_index=index,
            )
            if not audio_payload_result:
                await logger.awarning(
                    "[Reddit] Failed to fetch HLS audio payload",
                    source_url=source.audio_url,
                    video_url=source.url,
                    source_index=index,
                )
                return await cls._download_fallback_source(source, index, prefix, max_size, label)

            audio_payload, _ = audio_payload_result

        remuxed_payload = await asyncio.to_thread(cls._remux_hls_payloads_to_mp4, video_payload, audio_payload)
        if not remuxed_payload:
            await logger.awarning(
                "[Reddit] Failed to remux HLS media",
                source_url=source.url,
                audio_url=source.audio_url,
                source_index=index,
            )
            return await cls._download_fallback_source(source, index, prefix, max_size, label)

        if max_size and len(remuxed_payload) > max_size:
            await logger.adebug(
                "[Reddit] Remuxed HLS media too large", size=len(remuxed_payload), source_url=source.url
            )
            return await cls._download_fallback_source(source, index, prefix, max_size, label)

        thumbnail: InputFile | None = None
        if source.thumbnail_url and source.kind == MediaKind.VIDEO:
            thumbnail = await cls._download_thumbnail(source.thumbnail_url, label, index, prefix)

        filename = f"{prefix}_{index}.mp4"
        return MediaItem(
            kind=source.kind,
            file=BufferedInputFile(remuxed_payload, filename),
            filename=filename,
            source_url=source.url,
            thumbnail=thumbnail,
            duration=source.duration,
            width=source.width,
            height=source.height,
        )

    @classmethod
    async def _download_fallback_source(
        cls, source: MediaSource, index: int, prefix: str, max_size: int | None, label: str
    ) -> MediaItem | None:
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
        return await super()._download_source(fallback_source, index, prefix, max_size, label)

    @staticmethod
    def _remux_hls_payloads_to_mp4(video_payload: bytes, audio_payload: bytes | None) -> bytes | None:
        with tempfile.TemporaryDirectory(prefix="korone-reddit-hls-") as temp_dir:
            temp_dir_path = Path(temp_dir)
            video_input_path = temp_dir_path / "video.ts"
            video_input_path.write_bytes(video_payload)

            command = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(video_input_path)]
            if audio_payload is not None:
                audio_input_path = temp_dir_path / "audio.aac"
                audio_input_path.write_bytes(audio_payload)
                command.extend(["-i", str(audio_input_path)])

            output_path = temp_dir_path / "output.mp4"
            command.extend(["-c", "copy", str(output_path)])

            try:
                result = subprocess.run(command, capture_output=True, text=True, check=False)
            except OSError:
                return None

            if result.returncode != 0 or not output_path.exists():
                return None

            return output_path.read_bytes()

    @classmethod
    async def _download_media(cls, sources: list[MediaSource]) -> list[MediaItem]:
        return await cls.download_media(
            sources, filename_prefix="reddit_media", max_size=TELEGRAM_MEDIA_MAX_FILE_SIZE_BYTES, log_label="Reddit"
        )
