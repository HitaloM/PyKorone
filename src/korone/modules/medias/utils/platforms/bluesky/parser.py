from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from korone.modules.medias.utils.types import MediaKind, MediaSource

if TYPE_CHECKING:
    import re


def extract_handle_and_rkey(url: str, pattern: re.Pattern[str]) -> tuple[str | None, str | None]:
    match = pattern.search(url)
    if not match:
        return None, None
    return match.group("handle"), match.group("rkey")


def extract_post(data: dict[str, Any]) -> dict[str, Any] | None:
    thread = data.get("thread") if isinstance(data, dict) else None
    if not isinstance(thread, dict):
        return None
    post = thread.get("post")
    return post if isinstance(post, dict) else None


def extract_author(post: dict[str, Any]) -> tuple[str, str, str]:
    author_raw = post.get("author")
    author = author_raw if isinstance(author_raw, dict) else {}
    author_name = author.get("displayName") or ""
    author_handle = author.get("handle") or ""
    author_did = author.get("did") or ""
    return str(author_name), str(author_handle), str(author_did)


def extract_text(post: dict[str, Any]) -> str:
    record_raw = post.get("record")
    record = record_raw if isinstance(record_raw, dict) else {}
    text = record.get("text") or ""
    return str(text)


def build_post_url(handle: str, rkey: str) -> str:
    return f"https://bsky.app/profile/{quote(handle)}/post/{quote(rkey)}"


def extract_embed_view(post: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
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


def extract_media_sources(
    embed_view: dict[str, Any], embed_type: str, author_did: str, pds_url: str | None
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
            MediaSource(kind=kind, url=url, thumbnail_url=thumbnail_url, duration=duration, width=width, height=height)
        )

    if embed_type == "app.bsky.embed.images#view":
        images_raw = embed_view.get("images")
        images: list[dict[str, Any]] = (
            [image for image in images_raw if isinstance(image, dict)] if isinstance(images_raw, list) else []
        )
        for image in images:
            fullsize = image.get("fullsize") or image.get("thumb")
            if isinstance(fullsize, str):
                width, height = extract_aspect_ratio(image)
                _add(
                    MediaKind.PHOTO,
                    fullsize,
                    thumbnail_url=str(image.get("thumb")) if isinstance(image.get("thumb"), str) else None,
                    width=width,
                    height=height,
                )

    if embed_type == "app.bsky.embed.video#view":
        video_url = build_video_url(embed_view, author_did, pds_url)
        if video_url:
            width, height = extract_aspect_ratio(embed_view)
            thumbnail_url = embed_view.get("thumbnail")
            _add(
                MediaKind.VIDEO,
                video_url,
                thumbnail_url=str(thumbnail_url) if isinstance(thumbnail_url, str) else None,
                width=width,
                height=height,
            )

    return sources


def build_video_url(embed: dict[str, Any], author_did: str, pds_url: str | None) -> str | None:
    cid = embed.get("cid")
    if isinstance(cid, str) and author_did and pds_url:
        return f"{pds_url}/xrpc/com.atproto.sync.getBlob?did={quote(author_did)}&cid={quote(cid)}"
    return None


def extract_aspect_ratio(embed: dict[str, Any]) -> tuple[int | None, int | None]:
    aspect = embed.get("aspectRatio")
    if not isinstance(aspect, dict):
        return None, None
    return coerce_int(aspect.get("width")), coerce_int(aspect.get("height"))


def coerce_int(value: object) -> int | None:
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
