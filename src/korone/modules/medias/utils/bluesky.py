from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import quote

import aiohttp

from korone.constants import TELEGRAM_MEDIA_MAX_FILE_SIZE_BYTES
from korone.logger import get_logger
from korone.utils.aiohttp_session import HTTPClient

from .base import MediaKind, MediaPost, MediaProvider, MediaSource

if TYPE_CHECKING:
    from korone.utils.cached import JsonValue

    from .base import MediaItem

logger = get_logger(__name__)

BSKY_PUBLIC_API = "https://public.api.bsky.app/xrpc"
BSKY_RESOLVE_HANDLE = f"{BSKY_PUBLIC_API}/com.atproto.identity.resolveHandle"
BSKY_POST_THREAD = f"{BSKY_PUBLIC_API}/app.bsky.feed.getPostThread"
BSKY_PLC_DIRECTORY = "https://plc.directory"
HTTP_TIMEOUT = 25
HTTP_DOWNLOAD_TIMEOUT = 60


class BlueskyProvider(MediaProvider):
    name = "Bluesky"
    website = "Bluesky"
    pattern = re.compile(
        r"https?://(?:www\.)?bsky\.app/profile/(?P<handle>[^/]+)/post/(?P<rkey>[A-Za-z0-9]+)(?:\?[^\s]+)?",
        re.IGNORECASE,
    )

    @classmethod
    async def fetch(cls, url: str) -> MediaPost | None:
        handle, rkey = cls._extract_handle_and_rkey(url)
        if not handle or not rkey:
            return None

        did = await cls._resolve_handle(handle)
        if not did:
            return None

        uri = f"at://{did}/app.bsky.feed.post/{rkey}"
        thread = await cls._get_post_thread(uri)
        if not thread:
            return None

        post = cls._extract_post(thread)
        if not post:
            return None

        author_name, author_handle, author_did = cls._extract_author(post)
        text = cls._extract_text(post)
        post_url = cls._build_post_url(author_handle or handle, rkey)

        effective_did = author_did or did
        embed_view, embed_type = cls._extract_embed_view(post)
        if not embed_view or not embed_type:
            return None

        pds_url = None
        if embed_type == "app.bsky.embed.video#view":
            pds_url = await cls._resolve_pds_url(effective_did)
            if not pds_url:
                return None

        media_sources = cls._extract_media_sources(embed_view, embed_type, effective_did, pds_url)
        media = await cls._download_media(media_sources)
        if not media:
            return None

        return MediaPost(
            author_name=author_name or author_handle or "Bluesky",
            author_handle=author_handle or handle,
            text=text,
            url=post_url,
            website=cls.website,
            media=media,
        )

    @classmethod
    def _extract_handle_and_rkey(cls, url: str) -> tuple[str | None, str | None]:
        match = cls.pattern.search(url)
        if not match:
            return None, None
        return match.group("handle"), match.group("rkey")

    @staticmethod
    async def _resolve_handle(handle: str) -> str | None:
        timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT)
        params = {"handle": handle}
        try:
            session = await HTTPClient.get_session()
            async with session.get(BSKY_RESOLVE_HANDLE, timeout=timeout, params=params) as response:
                if response.status != 200:
                    await logger.adebug("[Bluesky] Resolve handle failed", status=response.status, handle=handle)
                    return None
                data = await response.json()
                return str(data.get("did")) if isinstance(data, dict) else None
        except (aiohttp.ClientError, aiohttp.ContentTypeError) as exc:
            await logger.aerror("[Bluesky] Resolve handle error", error=str(exc))
            return None

    @staticmethod
    async def _resolve_pds_url(did: str) -> str | None:
        timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT)
        if did.startswith("did:plc:"):
            url = f"{BSKY_PLC_DIRECTORY}/{did}"
        elif did.startswith("did:web:"):
            domain = did.removeprefix("did:web:")
            url = f"https://{domain}/.well-known/did.json"
        else:
            return None
        try:
            session = await HTTPClient.get_session()
            async with session.get(url, timeout=timeout) as response:
                if response.status != 200:
                    await logger.adebug("[Bluesky] PLC directory lookup failed", status=response.status, did=did)
                    return None
                data = await response.json()
                if not isinstance(data, dict):
                    return None
                services = data.get("service")
                if not isinstance(services, list):
                    return None
                for service in services:
                    if isinstance(service, dict) and service.get("id") == "#atproto_pds":
                        endpoint = service.get("serviceEndpoint")
                        return str(endpoint) if isinstance(endpoint, str) else None
                return None
        except (aiohttp.ClientError, aiohttp.ContentTypeError) as exc:
            await logger.aerror("[Bluesky] PDS resolution error", error=str(exc))
            return None

    @staticmethod
    async def _get_post_thread(uri: str) -> dict[str, JsonValue] | None:
        timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT)
        params = {"uri": uri, "depth": 0}
        try:
            session = await HTTPClient.get_session()
            async with session.get(BSKY_POST_THREAD, timeout=timeout, params=params) as response:
                if response.status != 200:
                    await logger.adebug("[Bluesky] Post thread failed", status=response.status, uri=uri)
                    return None
                data = await response.json()
                return cast("dict[str, JsonValue]", data)
        except (aiohttp.ClientError, aiohttp.ContentTypeError) as exc:
            await logger.aerror("[Bluesky] Post thread error", error=str(exc))
            return None

    @staticmethod
    def _extract_post(data: dict[str, Any]) -> dict[str, Any] | None:
        thread = data.get("thread") if isinstance(data, dict) else None
        if not isinstance(thread, dict):
            return None
        post = thread.get("post")
        return post if isinstance(post, dict) else None

    @staticmethod
    def _extract_author(post: dict[str, Any]) -> tuple[str, str, str]:
        author_raw = post.get("author")
        author = author_raw if isinstance(author_raw, dict) else {}
        author_name = author.get("displayName") or ""
        author_handle = author.get("handle") or ""
        author_did = author.get("did") or ""
        return str(author_name), str(author_handle), str(author_did)

    @staticmethod
    def _extract_text(post: dict[str, Any]) -> str:
        record_raw = post.get("record")
        record = record_raw if isinstance(record_raw, dict) else {}
        text = record.get("text") or ""
        return str(text)

    @staticmethod
    def _build_post_url(handle: str, rkey: str) -> str:
        return f"https://bsky.app/profile/{quote(handle)}/post/{quote(rkey)}"

    @staticmethod
    def _extract_embed_view(post: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
        embed = post.get("embed") if isinstance(post.get("embed"), dict) else None
        if not isinstance(embed, dict):
            return None, ""

        embed_view: dict[str, Any] = embed
        embed_type: str = ""
        embed_type_raw = embed_view.get("$type")
        if isinstance(embed_type_raw, str):
            embed_type = embed_type_raw
        if embed_type == "app.bsky.embed.recordWithMedia#view":
            media = embed_view.get("media") if isinstance(embed_view.get("media"), dict) else None
            if not isinstance(media, dict):
                return None, ""
            embed_view = media
            embed_type_raw = embed_view.get("$type")
            embed_type = embed_type_raw if isinstance(embed_type_raw, str) else ""

        return embed_view, embed_type

    @classmethod
    def _extract_media_sources(
        cls, embed_view: dict[str, Any], embed_type: str, author_did: str, pds_url: str | None
    ) -> list[MediaSource]:
        sources: list[MediaSource] = []
        seen: set[str] = set()

        def _add(
            kind: MediaKind,
            url: str,
            *,
            thumbnail_url: str | None = None,
            duration: int | None = None,
            width: int | None = None,
            height: int | None = None,
        ) -> None:
            if not url or url in seen:
                return
            seen.add(url)
            sources.append(
                MediaSource(
                    kind=kind, url=url, thumbnail_url=thumbnail_url, duration=duration, width=width, height=height
                )
            )

        if embed_type == "app.bsky.embed.images#view":
            images_raw = embed_view.get("images")
            images: list[dict[str, Any]] = (
                [image for image in images_raw if isinstance(image, dict)] if isinstance(images_raw, list) else []
            )
            for image in images:
                fullsize = image.get("fullsize") or image.get("thumb")
                if isinstance(fullsize, str):
                    width, height = cls._extract_aspect_ratio(image)
                    _add(
                        MediaKind.PHOTO,
                        fullsize,
                        thumbnail_url=str(image.get("thumb")) if isinstance(image.get("thumb"), str) else None,
                        width=width,
                        height=height,
                    )

        if embed_type == "app.bsky.embed.video#view":
            video_url = cls._build_video_url(embed_view, author_did, pds_url)
            if video_url:
                width, height = cls._extract_aspect_ratio(embed_view)
                thumbnail_url = embed_view.get("thumbnail")
                _add(
                    MediaKind.VIDEO,
                    video_url,
                    thumbnail_url=str(thumbnail_url) if isinstance(thumbnail_url, str) else None,
                    width=width,
                    height=height,
                )

        return sources

    @staticmethod
    def _build_video_url(embed: dict[str, Any], author_did: str, pds_url: str | None) -> str | None:
        cid = embed.get("cid")
        if isinstance(cid, str) and author_did and pds_url:
            return f"{pds_url}/xrpc/com.atproto.sync.getBlob?did={quote(author_did)}&cid={quote(cid)}"
        return None

    @classmethod
    def _extract_aspect_ratio(cls, embed: dict[str, Any]) -> tuple[int | None, int | None]:
        aspect = embed.get("aspectRatio")
        if not isinstance(aspect, dict):
            return None, None
        return cls._coerce_int(aspect.get("width")), cls._coerce_int(aspect.get("height"))

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
            sources, filename_prefix="bsky_media", max_size=TELEGRAM_MEDIA_MAX_FILE_SIZE_BYTES, log_label="Bluesky"
        )
