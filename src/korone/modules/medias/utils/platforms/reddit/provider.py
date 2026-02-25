from __future__ import annotations

import re
from typing import TYPE_CHECKING
from urllib.parse import quote, urljoin, urlparse, urlunparse

import aiohttp
from lxml import html as lxml_html

from korone.constants import TELEGRAM_MEDIA_MAX_FILE_SIZE_BYTES
from korone.logger import get_logger
from korone.modules.medias.utils.provider_base import MediaProvider
from korone.modules.medias.utils.types import MediaKind, MediaPost, MediaSource
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
from .types import _PostRef, _ResolvedVideo, _ScrapedPost

if TYPE_CHECKING:
    from korone.modules.medias.utils.types import MediaItem

logger = get_logger(__name__)


class RedditProvider(RedlibAnubisBypassMixin, MediaProvider):
    name = "Reddit"
    website = "Reddit"

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
        candidates = [*REDLIB_INSTANCES]
        unique: list[str] = []
        seen: set[str] = set()
        for candidate in candidates:
            normalized = candidate.rstrip("/")
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            unique.append(normalized)
        return unique

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

        def add(
            kind: MediaKind,
            url: str | None,
            *,
            thumbnail_url: str | None = None,
            width: int | None = None,
            height: int | None = None,
        ) -> None:
            if not url:
                return
            normalized_url = cls._normalize_media_url(base_url, url)
            if not normalized_url or normalized_url in seen:
                return

            seen.add(normalized_url)
            normalized_thumb = cls._normalize_media_url(base_url, thumbnail_url) if thumbnail_url else None
            sources.append(
                MediaSource(kind=kind, url=normalized_url, thumbnail_url=normalized_thumb, width=width, height=height)
            )

        if post_type == "gallery":
            for gallery_url in cls._extract_gallery_urls(tree):
                add(MediaKind.PHOTO, gallery_url)

        if post_type == "image" and not sources:
            image_url = cls._extract_image_url(tree)
            add(MediaKind.PHOTO, image_url)

        if post_type in {"video", "gif"} and not sources:
            video = await cls._extract_video_source(tree, html_content, base_url)
            if video:
                add(
                    MediaKind.VIDEO,
                    video.url,
                    thumbnail_url=video.thumbnail_url,
                    width=video.width,
                    height=video.height,
                )

        if not sources:
            for gallery_url in cls._extract_gallery_urls(tree):
                add(MediaKind.PHOTO, gallery_url)

        if not sources:
            add(MediaKind.PHOTO, cls._extract_image_url(tree))

        if not sources:
            video = await cls._extract_video_source(tree, html_content, base_url)
            if video:
                add(
                    MediaKind.VIDEO,
                    video.url,
                    thumbnail_url=video.thumbnail_url,
                    width=video.width,
                    height=video.height,
                )

        return sources

    @classmethod
    def _extract_gallery_urls(cls, tree: lxml_html.HtmlElement) -> list[str]:
        urls: list[str] = []
        gallery_nodes = tree.xpath("//div[contains(@class, 'gallery')]//figure")
        for figure in gallery_nodes:
            href = cls._first_non_empty(figure.xpath(".//a/@href"))
            src = cls._first_non_empty(figure.xpath(".//img[@alt='Gallery image']/@src"))
            selected = href or src
            if selected:
                urls.append(selected)
        return urls

    @classmethod
    def _extract_image_url(cls, tree: lxml_html.HtmlElement) -> str | None:
        return (
            cls._first_non_empty(
                tree.xpath(
                    "//div[contains(@class, 'post_media_content')]//a[contains(@class, 'post_media_image')]/@href"
                )
            )
            or cls._first_non_empty(tree.xpath("//div[contains(@class, 'post_media_content')]//img/@src"))
            or cls._first_non_empty(tree.xpath("//meta[@property='og:image']/@content"))
        )

    @classmethod
    async def _extract_video_source(
        cls, tree: lxml_html.HtmlElement, html_content: str, base_url: str
    ) -> _ResolvedVideo | None:
        video_nodes = tree.xpath(
            "//div[contains(@class, 'post_media_content')]//video[contains(@class, 'post_media_video')]"
        )
        if video_nodes:
            video_node = video_nodes[0]
            poster = video_node.get("poster")
            width = cls._coerce_int(video_node.get("width"))
            height = cls._coerce_int(video_node.get("height"))

            direct_mp4_sources = [video_node.get("src") or ""]
            direct_mp4_sources.extend(
                str(source)
                for source in video_node.xpath(".//source[@type='video/mp4' or starts-with(@type, 'video/mp4')]/@src")
            )
            for source in direct_mp4_sources:
                normalized = cls._normalize_media_url(base_url, source)
                if normalized:
                    return _ResolvedVideo(url=normalized, thumbnail_url=poster, width=width, height=height)

            hls_source = cls._first_non_empty(
                video_node.xpath(
                    ".//source[@type='application/vnd.apple.mpegurl' "
                    "or starts-with(@type, 'application/vnd.apple.mpegurl')]/@src"
                )
            )
            if hls_source:
                resolved = await cls._resolve_hls_to_mp4(cls._normalize_media_url(base_url, hls_source))
                if resolved:
                    video_url, resolved_width, resolved_height = resolved
                    return _ResolvedVideo(
                        url=video_url,
                        thumbnail_url=poster,
                        width=resolved_width or width,
                        height=resolved_height or height,
                    )

        mp4_match = cls._video_regex.search(html_content)
        if mp4_match and mp4_match.group(1):
            normalized = cls._normalize_media_url(base_url, mp4_match.group(1))
            if normalized:
                return _ResolvedVideo(url=normalized)

        playlist_match = cls._playlist_regex.search(html_content)
        if playlist_match and playlist_match.group(1):
            resolved = await cls._resolve_hls_to_mp4(cls._normalize_media_url(base_url, playlist_match.group(1)))
            if resolved:
                video_url, width, height = resolved
                return _ResolvedVideo(url=video_url, width=width, height=height)

        return None

    @classmethod
    async def _resolve_hls_to_mp4(cls, hls_url: str | None) -> tuple[str, int | None, int | None] | None:
        if not hls_url:
            return None

        playlist = await cls._fetch_text(hls_url)
        if not playlist:
            return None

        best_variant: str | None = None
        best_bandwidth = -1
        best_width: int | None = None
        best_height: int | None = None

        stream_info: str | None = None
        for raw_line in playlist.splitlines():
            line = raw_line.strip()
            if not line:
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
            if bandwidth > best_bandwidth:
                best_bandwidth = bandwidth
                best_variant = line
                best_width = width
                best_height = height

            if best_variant is None:
                best_variant = line
                best_width = width
                best_height = height

            stream_info = None

        if not best_variant:
            return None

        variant_url = cls._join_hls_url(hls_url, best_variant)
        if not variant_url:
            return None

        parsed_variant = urlparse(variant_url)
        if parsed_variant.path.endswith(".m3u8"):
            mp4_path = f"{parsed_variant.path[:-5]}.mp4"
            variant_url = urlunparse(parsed_variant._replace(path=mp4_path))

        return variant_url, best_width, best_height

    @classmethod
    async def _fetch_text(cls, url: str) -> str | None:
        try:
            text = await client.fetch_text(url, headers=cls._DEFAULT_HEADERS, cookies=REDLIB_REQUEST_COOKIES)
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
    def _normalize_media_url(cls, base_url: str, candidate: str | None) -> str:
        return parser.normalize_media_url(base_url, candidate)

    @staticmethod
    def _first_non_empty(values: list[str]) -> str | None:
        return parser.first_non_empty(values)

    @staticmethod
    def _coerce_int(value: object) -> int | None:
        return parser.coerce_int(value)

    @classmethod
    async def _download_media(cls, sources: list[MediaSource]) -> list[MediaItem]:
        return await cls.download_media(
            sources, filename_prefix="reddit_media", max_size=TELEGRAM_MEDIA_MAX_FILE_SIZE_BYTES, log_label="Reddit"
        )
