from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from korone.modules.medias.utils.parsing import coerce_int, coerce_str, dict_list, dict_or_empty
from korone.modules.medias.utils.types import MediaKind, MediaSource

if TYPE_CHECKING:
    import re


def extract_handle_and_rkey(url: str, pattern: re.Pattern[str]) -> tuple[str | None, str | None]:
    match = pattern.search(url)
    if not match:
        return None, None
    return match.group("handle"), match.group("rkey")


def extract_post(data: dict[str, Any]) -> dict[str, Any] | None:
    thread = dict_or_empty(data.get("thread"))
    post = thread.get("post")
    return post if isinstance(post, dict) else None


def extract_author(post: dict[str, Any]) -> tuple[str, str, str]:
    author = dict_or_empty(post.get("author"))
    author_name = coerce_str(author.get("displayName")) or ""
    author_handle = coerce_str(author.get("handle")) or ""
    author_did = coerce_str(author.get("did")) or ""
    return author_name, author_handle, author_did


def extract_text(post: dict[str, Any]) -> str:
    record = dict_or_empty(post.get("record"))
    return coerce_str(record.get("text")) or ""


def build_post_url(handle: str, rkey: str) -> str:
    return f"https://bsky.app/profile/{quote(handle)}/post/{quote(rkey)}"


def extract_embed_view(post: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
    embed_view = dict_or_empty(post.get("embed"))
    if not embed_view:
        return None, ""

    embed_type = coerce_str(embed_view.get("$type")) or ""

    if embed_type == "app.bsky.embed.recordWithMedia#view":
        embed_view = dict_or_empty(embed_view.get("media"))
        if not embed_view:
            return None, ""
        embed_type = coerce_str(embed_view.get("$type")) or ""

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
        for image in dict_list(embed_view.get("images")):
            fullsize = coerce_str(image.get("fullsize") or image.get("thumb"))
            if not fullsize:
                continue

            width, height = extract_aspect_ratio(image)
            _add(MediaKind.PHOTO, fullsize, thumbnail_url=coerce_str(image.get("thumb")), width=width, height=height)

    if embed_type == "app.bsky.embed.video#view":
        video_url = build_video_url(embed_view, author_did, pds_url)
        if video_url:
            width, height = extract_aspect_ratio(embed_view)
            _add(
                MediaKind.VIDEO,
                video_url,
                thumbnail_url=coerce_str(embed_view.get("thumbnail")),
                width=width,
                height=height,
            )

    return sources


def build_video_url(embed: dict[str, Any], author_did: str, pds_url: str | None) -> str | None:
    cid = coerce_str(embed.get("cid"))
    if cid and author_did and pds_url:
        return f"{pds_url}/xrpc/com.atproto.sync.getBlob?did={quote(author_did)}&cid={quote(cid)}"
    return None


def extract_aspect_ratio(embed: dict[str, Any]) -> tuple[int | None, int | None]:
    aspect = embed.get("aspectRatio")
    if not isinstance(aspect, dict):
        return None, None
    return coerce_int(aspect.get("width")), coerce_int(aspect.get("height"))
