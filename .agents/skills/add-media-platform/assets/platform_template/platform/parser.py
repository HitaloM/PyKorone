from typing import Any

from korone.modules.medias.utils.parsing import coerce_int, coerce_str, dict_list, dict_or_empty
from korone.modules.medias.utils.types import MediaKind, MediaSource

from .constants import PATTERN


def extract_post_id(url: str) -> str | None:
    match = PATTERN.search(url)
    return coerce_str(match.group("id")) if match else None


def extract_media_sources(payload: dict[str, Any]) -> list[MediaSource]:
    sources: list[MediaSource] = []

    for item in dict_list(payload.get("media")):
        media_url = coerce_str(item.get("url"))
        media_type = coerce_str(item.get("type"))
        if not media_url or media_type not in {"image", "video"}:
            continue

        sources.append(
            MediaSource(
                kind=MediaKind.VIDEO if media_type == "video" else MediaKind.PHOTO,
                url=media_url,
                thumbnail_url=coerce_str(item.get("thumbnail_url")),
                duration=coerce_int(item.get("duration")),
                width=coerce_int(item.get("width")),
                height=coerce_int(item.get("height")),
            )
        )

    return sources


def extract_author(payload: dict[str, Any]) -> str:
    return coerce_str(dict_or_empty(payload.get("author")).get("handle")) or ""


def extract_text(payload: dict[str, Any]) -> str:
    return coerce_str(payload.get("text")) or ""
