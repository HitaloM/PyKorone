from __future__ import annotations

import re
from typing import Any, cast

from korone.modules.medias.utils.types import MediaKind, MediaSource


def extract_status_id_and_handle(url: str) -> tuple[str | None, str | None]:
    match = re.search(
        r"https?://(?:www\.)?(?:x\.com|twitter\.com)/(?:i/web/)?(?:(?P<handle>[A-Za-z0-9_]{1,15})/)?status/(?P<id>\d+)",
        url,
        re.IGNORECASE,
    )
    if not match:
        return None, None

    status_id = match.group("id")
    handle = match.group("handle")
    return status_id, handle


def extract_tweet_payload(data: dict[str, Any]) -> dict[str, Any] | None:
    if "tweet" in data and isinstance(data["tweet"], dict):
        return data["tweet"]
    if "data" in data and isinstance(data["data"], dict):
        return data["data"]
    if "tweet" not in data and "data" not in data:
        return data
    return None


def extract_author(tweet: dict[str, Any]) -> tuple[str, str]:
    author = tweet.get("author") or tweet.get("user") or {}
    author_name = author.get("name") or tweet.get("author_name") or tweet.get("user_name") or ""
    author_handle = (
        author.get("screen_name")
        or author.get("username")
        or tweet.get("author_handle")
        or tweet.get("user_screen_name")
        or ""
    )
    author_handle = author_handle.lstrip("@") if author_handle else ""
    return str(author_name), str(author_handle)


def extract_text(tweet: dict[str, Any]) -> str:
    text = tweet.get("text") or tweet.get("full_text") or tweet.get("content") or ""
    return str(text)


def extract_post_url(tweet: dict[str, Any], status_id: str, handle: str | None, fallback: str) -> str:
    url = tweet.get("url") or tweet.get("tweet_url") or ""
    if url:
        return str(url)
    if handle:
        return f"https://x.com/{handle}/status/{status_id}"
    return fallback


def extract_media_sources(tweet: dict[str, Any]) -> list[MediaSource]:
    media = tweet.get("media") or {}
    sources: list[MediaSource] = []
    seen: set[str] = set()

    def _ensure_list(value: object) -> list[dict[str, Any]]:
        if isinstance(value, list):
            return [cast("dict[str, Any]", item) for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            return [cast("dict[str, Any]", value)]
        return []

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

    def _extract_metadata(item: dict[str, Any]) -> tuple[str | None, int | None, int | None, int | None]:
        thumbnail_url = item.get("thumbnail_url") or item.get("thumb") or item.get("preview_image_url")
        return (
            str(thumbnail_url) if isinstance(thumbnail_url, str) else None,
            coerce_int(item.get("duration")),
            coerce_int(item.get("width")),
            coerce_int(item.get("height")),
        )

    for photo in _ensure_list(media.get("photos")) + _ensure_list(media.get("images")):
        url = photo.get("url") or photo.get("src") or photo.get("source")
        if isinstance(url, str):
            thumbnail_url, duration, width, height = _extract_metadata(photo)
            _add(MediaKind.PHOTO, url, thumbnail_url=thumbnail_url, duration=duration, width=width, height=height)

    for video in _ensure_list(media.get("videos")) + _ensure_list(media.get("video")):
        url = pick_video_url(video)
        if url:
            thumbnail_url, duration, width, height = _extract_metadata(video)
            _add(MediaKind.VIDEO, url, thumbnail_url=thumbnail_url, duration=duration, width=width, height=height)

    for item in _ensure_list(media.get("all")):
        kind = MediaKind.VIDEO if item.get("type") in {"video", "gif"} else MediaKind.PHOTO
        url = pick_video_url(item) if kind == MediaKind.VIDEO else None
        if not url:
            url = item.get("url") or item.get("src") or item.get("source")
        if not isinstance(url, str):
            continue

        thumbnail_url, duration, width, height = _extract_metadata(item)
        _add(kind, url, thumbnail_url=thumbnail_url, duration=duration, width=width, height=height)

    if not sources:
        media_url = tweet.get("media_url") or tweet.get("media_url_https")
        if isinstance(media_url, str):
            _add(MediaKind.PHOTO, media_url)

    return sources


def pick_video_url(video: dict[str, Any]) -> str | None:
    direct_url = video.get("url") or video.get("src") or video.get("source")
    if isinstance(direct_url, str):
        return direct_url

    variants = video.get("variants")
    if not isinstance(variants, list):
        return None

    best_url = None
    best_bitrate = -1
    for variant in variants:
        url = variant.get("url")
        if not isinstance(url, str):
            continue
        bitrate = variant.get("bitrate")
        if isinstance(bitrate, int) and bitrate > best_bitrate:
            best_bitrate = bitrate
            best_url = url
        if best_url is None:
            best_url = url
    return best_url


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
