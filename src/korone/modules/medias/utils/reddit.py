from __future__ import annotations

import asyncio
import hashlib
import html
import re
from dataclasses import dataclass
from time import perf_counter
from typing import TYPE_CHECKING
from urllib.parse import parse_qs, quote, urldefrag, urljoin, urlparse, urlunparse

import aiohttp
import orjson
from lxml import html as lxml_html

from korone.constants import TELEGRAM_MEDIA_MAX_FILE_SIZE_BYTES
from korone.logger import get_logger
from korone.utils.aiohttp_session import HTTPClient

from .base import MediaKind, MediaPost, MediaProvider, MediaSource

if TYPE_CHECKING:
    from .base import MediaItem

logger = get_logger(__name__)

REDLIB_INSTANCES = ("https://redlib.catsarch.com", "https://redlib.4o1x5.dev", "https://l.opnxng.com")
REDDIT_PATTERN_HOSTS = tuple(urlparse(instance).netloc for instance in REDLIB_INSTANCES)
REDDIT_PATTERN_HOSTS_REGEX = "|".join(re.escape(host) for host in REDDIT_PATTERN_HOSTS)
ANUBIS_PASS_CHALLENGE_PATH = "/.within.website/x/cmd/anubis/api/pass-challenge"

REDLIB_REQUEST_COOKIES = {"use_hls": "on", "hide_hls_notification": "on"}


@dataclass(frozen=True, slots=True)
class _PostRef:
    kind: str
    name: str | None
    post_id: str


@dataclass(frozen=True, slots=True)
class _ResolvedVideo:
    url: str
    thumbnail_url: str | None = None
    width: int | None = None
    height: int | None = None


@dataclass(frozen=True, slots=True)
class _ScrapedPost:
    author: str
    subreddit: str
    title: str
    post_url: str
    media_sources: list[MediaSource]


@dataclass(frozen=True, slots=True)
class _AnubisChallengeInfo:
    algorithm: str
    difficulty: int
    challenge_id: str
    random_data: str
    pass_url: str
    redir: str


class RedditProvider(MediaProvider):
    name = "Reddit"
    website = "Reddit"

    pattern = re.compile(
        rf"https?://(?:"
        rf"(?:www\.|old\.|new\.|np\.)?reddit\.com/(?:(?:r|user)/[^/\s]+/comments/[A-Za-z0-9]+(?:/[^\s?#]*)?|comments/[A-Za-z0-9]+(?:/[^\s?#]*)?)"
        rf"|(?:www\.)?redd\.it/[A-Za-z0-9]+(?:/[^\s?#]*)?"
        rf"|(?:{REDDIT_PATTERN_HOSTS_REGEX}|(?:[A-Za-z0-9-]+\.)?redlib\.[A-Za-z0-9.-]+)/(?:(?:r|user)/[^/\s]+/comments/[A-Za-z0-9]+(?:/[^\s?#]*)?|comments/[A-Za-z0-9]+(?:/[^\s?#]*)?)"
        rf")(?:\?[^\s#]*)?(?:#[^\s]*)?",
        re.IGNORECASE,
    )
    _post_type_regex = re.compile(r"post_type:\s*(\w+)", re.IGNORECASE)
    _video_regex = re.compile(r'(?s)<source\s+[^>]*src="([^"]+)"[^>]*type="video/mp4"')
    _playlist_regex = re.compile(r'(?s)<source\s+[^>]*src="([^"]+)"[^>]*type="application/vnd\.apple\.mpegurl"')
    _json_script_regex_template = r'(?is)<script[^>]*\bid=["\']{script_id}["\'][^>]*>(.*?)</script>'
    _meta_refresh_regex = re.compile(r'(?is)<meta[^>]*http-equiv=["\']refresh["\'][^>]*content=["\']([^"\']+)["\']')
    _block_markers = ("anubis_challenge", "making sure you're not a bot", "<title>403")

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
        candidate = post_id.strip()
        if not candidate:
            return None

        if re.fullmatch(r"[A-Za-z0-9]+", candidate):
            return candidate
        return None

    @staticmethod
    def _ensure_url_scheme(url: str) -> str:
        if url.startswith(("http://", "https://")):
            return url
        return f"https://{url.lstrip('/')}"

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
        async with session.get(
            url, headers=headers, cookies=REDLIB_REQUEST_COOKIES, allow_redirects=True, timeout=cls._DEFAULT_TIMEOUT
        ) as response:
            if response.status != 200:
                await logger.adebug("[Reddit] Non-200 Redlib response", status=response.status, url=url)
                return None

            html_content = await response.text()
            return {"html": html_content, "base_url": str(response.url)}

    @classmethod
    async def _solve_anubis_challenge(
        cls, session: aiohttp.ClientSession, *, challenge_html: str, challenge_url: str, headers: dict[str, str]
    ) -> dict[str, str] | None:
        info = cls._extract_anubis_challenge_info(challenge_html, challenge_url)
        if not info:
            return None

        params: dict[str, str]
        if info.algorithm == "metarefresh":
            await asyncio.sleep((max(info.difficulty, 0) * 0.8) + 0.1)
            params = {"id": info.challenge_id, "challenge": info.random_data, "redir": info.redir}
        elif info.algorithm == "preact":
            await asyncio.sleep((max(info.difficulty, 0) * 0.125) + 0.05)
            result = hashlib.sha256(info.random_data.encode("utf-8")).hexdigest()
            params = {"id": info.challenge_id, "result": result, "redir": info.redir}
        elif info.algorithm in {"fast", "slow"}:
            started_at = perf_counter()
            solved = await asyncio.to_thread(cls._solve_pow_challenge, info.random_data, info.difficulty)
            if not solved:
                await logger.adebug(
                    "[Reddit] Anubis PoW challenge not solved",
                    url=challenge_url,
                    algorithm=info.algorithm,
                    difficulty=info.difficulty,
                )
                return None
            response_hash, nonce = solved
            elapsed_time = max(1, int((perf_counter() - started_at) * 1000))
            params = {
                "id": info.challenge_id,
                "response": response_hash,
                "nonce": str(nonce),
                "redir": info.redir,
                "elapsedTime": str(elapsed_time),
            }
        else:
            await logger.adebug("[Reddit] Unsupported Anubis challenge", algorithm=info.algorithm, url=challenge_url)
            return None

        try:
            async with session.get(
                info.pass_url,
                headers=headers,
                cookies=REDLIB_REQUEST_COOKIES,
                params=params,
                allow_redirects=True,
                timeout=cls._DEFAULT_TIMEOUT,
            ) as response:
                if response.status != 200:
                    await logger.adebug(
                        "[Reddit] Failed to pass Anubis challenge",
                        status=response.status,
                        url=info.pass_url,
                        algorithm=info.algorithm,
                    )
                    return None

                html_content = await response.text()
                if cls._looks_like_block_page(html_content):
                    await logger.adebug(
                        "[Reddit] Anubis challenge solved but page still blocked",
                        url=info.pass_url,
                        algorithm=info.algorithm,
                    )
                    return None

                return {"html": html_content, "base_url": str(response.url)}
        except aiohttp.ClientError as exc:
            await logger.aerror("[Reddit] Failed during Anubis challenge solve", error=str(exc), url=info.pass_url)
            return None

    @classmethod
    def _extract_anubis_challenge_info(cls, html_content: str, challenge_url: str) -> _AnubisChallengeInfo | None:
        anubis_payload = cls._extract_json_script(html_content, "anubis_challenge")
        if isinstance(anubis_payload, dict):
            rules = anubis_payload.get("rules")
            challenge = anubis_payload.get("challenge")
            if isinstance(rules, dict) and isinstance(challenge, dict):
                algorithm = str(rules.get("algorithm") or challenge.get("method") or "").strip().lower()
                challenge_id = str(challenge.get("id") or "").strip()
                random_data = str(challenge.get("randomData") or "").strip()
                difficulty = cls._coerce_int(rules.get("difficulty"))
                if difficulty is None:
                    difficulty = cls._coerce_int(challenge.get("difficulty"))
                difficulty = max(difficulty or 0, 0)

                if algorithm and challenge_id and random_data:
                    base_prefix = cls._extract_json_script(html_content, "anubis_base_prefix")
                    prefix = base_prefix if isinstance(base_prefix, str) else ""
                    pass_url = cls._extract_meta_refresh_pass_url(html_content, challenge_url)
                    if not pass_url:
                        pass_url = cls._build_anubis_pass_url(challenge_url, prefix)
                    redir = cls._extract_query_param(pass_url, "redir") or cls._build_challenge_redir(challenge_url)
                    return _AnubisChallengeInfo(
                        algorithm=algorithm,
                        difficulty=difficulty,
                        challenge_id=challenge_id,
                        random_data=random_data,
                        pass_url=pass_url,
                        redir=redir,
                    )

        preact_payload = cls._extract_json_script(html_content, "preact_info")
        if isinstance(preact_payload, dict):
            pass_url_raw = str(preact_payload.get("redir") or "").strip()
            random_data = str(preact_payload.get("challenge") or "").strip()
            difficulty = max(cls._coerce_int(preact_payload.get("difficulty")) or 0, 0)
            if pass_url_raw and random_data:
                pass_url = urljoin(challenge_url, pass_url_raw)
                challenge_id = cls._extract_query_param(pass_url, "id")
                redir = cls._extract_query_param(pass_url, "redir") or cls._build_challenge_redir(challenge_url)
                if challenge_id:
                    return _AnubisChallengeInfo(
                        algorithm="preact",
                        difficulty=difficulty,
                        challenge_id=challenge_id,
                        random_data=random_data,
                        pass_url=pass_url,
                        redir=redir,
                    )

        return None

    @classmethod
    def _extract_json_script(cls, html_content: str, script_id: str) -> object | None:
        pattern = cls._json_script_regex_template.format(script_id=re.escape(script_id))
        match = re.search(pattern, html_content)
        if not match:
            return None

        payload = html.unescape(match.group(1).strip())
        if not payload:
            return None

        try:
            return orjson.loads(payload)
        except orjson.JSONDecodeError:
            return None

    @classmethod
    def _extract_meta_refresh_pass_url(cls, html_content: str, challenge_url: str) -> str:
        match = cls._meta_refresh_regex.search(html_content)
        if not match:
            return ""

        content = html.unescape(match.group(1))
        url_match = re.search(r"(?i)\burl\s*=\s*(.+)$", content)
        if not url_match:
            return ""

        target = url_match.group(1).strip()
        if not target:
            return ""
        return urljoin(challenge_url, target)

    @staticmethod
    def _build_anubis_pass_url(challenge_url: str, base_prefix: str) -> str:
        prefix = base_prefix.strip()
        if prefix and not prefix.startswith("/"):
            prefix = f"/{prefix}"
        prefix = prefix.rstrip("/")
        return urljoin(challenge_url, f"{prefix}{ANUBIS_PASS_CHALLENGE_PATH}")

    @staticmethod
    def _extract_query_param(url: str, key: str) -> str:
        values = parse_qs(urlparse(url).query).get(key)
        if not values:
            return ""
        value = values[0]
        if not isinstance(value, str):
            return ""
        return value.strip()

    @staticmethod
    def _build_challenge_redir(challenge_url: str) -> str:
        parsed = urlparse(challenge_url)
        path = parsed.path or "/"
        if parsed.query:
            return f"{path}?{parsed.query}"
        return path

    @classmethod
    def _solve_pow_challenge(cls, random_data: str, difficulty: int) -> tuple[str, int] | None:
        if difficulty < 0:
            return None

        target_prefix = "0" * difficulty
        started_at = perf_counter()
        nonce = 0

        while perf_counter() - started_at <= 20.0:
            digest = hashlib.sha256(f"{random_data}{nonce}".encode()).hexdigest()
            if digest.startswith(target_prefix):
                return digest, nonce
            nonce += 1

        return None

    @classmethod
    def _looks_like_block_page(cls, html_content: str) -> bool:
        lowered = html_content.lower()
        return any(marker in lowered for marker in cls._block_markers)

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
            session = await HTTPClient.get_session()
            async with session.get(url, headers=cls._DEFAULT_HEADERS, cookies=REDLIB_REQUEST_COOKIES) as response:
                if response.status != 200:
                    await logger.adebug("[Reddit] Failed to fetch playlist", status=response.status, url=url)
                    return None
                return await response.text()
        except aiohttp.ClientError as exc:
            await logger.aerror("[Reddit] Playlist request failed", error=str(exc), url=url)
            return None

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
        if not candidate:
            return ""

        decoded = html.unescape(candidate.strip())
        if not decoded:
            return ""

        absolute = urljoin(base_url, decoded)
        absolute, _ = urldefrag(absolute)
        return absolute.strip()

    @staticmethod
    def _first_non_empty(values: list[str]) -> str | None:
        for value in values:
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    @staticmethod
    def _coerce_int(value: object) -> int | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            try:
                return int(float(value))
            except ValueError:
                return None
        return None

    @classmethod
    async def _download_media(cls, sources: list[MediaSource]) -> list[MediaItem]:
        return await cls.download_media(
            sources, filename_prefix="reddit_media", max_size=TELEGRAM_MEDIA_MAX_FILE_SIZE_BYTES, log_label="Reddit"
        )
