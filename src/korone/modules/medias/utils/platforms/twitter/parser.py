from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from korone.modules.medias.utils.parsing import coerce_int, coerce_str, dict_list, dict_or_empty
from korone.modules.medias.utils.types import MediaKind, MediaSource

if TYPE_CHECKING:
    from collections.abc import Iterator

_STATUS_URL_PATTERN = re.compile(
    r"https?://(?:www\.)?(?:x\.com|(?:www\.|mobile\.)?twitter\.com)/"
    r"(?:i/(?:web/)?|(?P<handle>[A-Za-z0-9_]{1,15})/)?status/(?P<id>\d+)",
    re.IGNORECASE,
)
_VIDEO_MEDIA_TYPES = {"video", "gif", "animated_gif"}


def extract_status_id_and_handle(url: str) -> tuple[str | None, str | None]:
    match = _STATUS_URL_PATTERN.search(url)
    if not match:
        return None, None

    status_id = match.group("id")
    handle = normalize_handle(match.group("handle"))
    return status_id, handle


def normalize_handle(value: object) -> str | None:
    if not isinstance(value, str):
        return None

    handle = value.strip().lstrip("@")
    if not handle:
        return None

    normalized = handle.lower()
    if normalized in {"i", "web"}:
        return None
    return handle


def extract_status_code(data: dict[str, Any]) -> int | None:
    return coerce_int(data.get("code"))


def extract_status_message(data: dict[str, Any]) -> str:
    return coerce_str(data.get("message")) or ""


def extract_tweet_payload(data: dict[str, Any]) -> dict[str, Any] | None:
    status_code = extract_status_code(data)
    if status_code is not None and status_code != 200:
        return None

    if "tweet" in data and isinstance(data["tweet"], dict):
        return data["tweet"]
    if "data" in data and isinstance(data["data"], dict):
        return data["data"]
    if "tweet" not in data and "data" not in data:
        return data
    return None


def extract_author(tweet: dict[str, Any]) -> tuple[str, str]:
    author = dict_or_empty(tweet.get("author"))
    if not author:
        author = dict_or_empty(tweet.get("user"))

    core = dict_or_empty(tweet.get("core"))
    user_results = dict_or_empty(core.get("user_results"))
    user_result = dict_or_empty(user_results.get("result"))
    user_legacy = dict_or_empty(user_result.get("legacy"))
    legacy = extract_legacy(tweet)

    author_name = (
        coerce_str(
            author.get("name")
            or tweet.get("author_name")
            or tweet.get("user_name")
            or user_legacy.get("name")
            or legacy.get("name")
        )
        or ""
    )
    author_handle = normalize_handle(
        author.get("screen_name")
        or author.get("username")
        or author.get("handle")
        or tweet.get("author_handle")
        or tweet.get("user_screen_name")
        or user_legacy.get("screen_name")
        or legacy.get("screen_name")
    )
    return author_name, author_handle or ""


def extract_text(tweet: dict[str, Any]) -> str:
    quoted_tweet = extract_quoted_tweet(tweet)
    note_tweet = dict_or_empty(tweet.get("note_tweet"))
    note_result = dict_or_empty(dict_or_empty(note_tweet.get("note_tweet_results")).get("result"))
    legacy = extract_legacy(tweet)

    note_text = coerce_str(note_result.get("text"))
    legacy_text = coerce_str(legacy.get("full_text"))
    fallback_text = coerce_str(
        tweet.get("text") or tweet.get("translation") or tweet.get("full_text") or tweet.get("content")
    )

    if note_text and quoted_tweet is None:
        return _strip_trailing_tco_link(note_text)
    if legacy_text:
        return _strip_trailing_tco_link(legacy_text)
    if fallback_text:
        return _strip_trailing_tco_link(fallback_text)
    return ""


def extract_quote(tweet: dict[str, Any]) -> tuple[str | None, str | None, str | None] | None:
    quoted_tweet = extract_quoted_tweet(tweet)
    if not quoted_tweet:
        return None

    quoted_legacy = extract_legacy(quoted_tweet)
    quoted_text = coerce_str(
        quoted_legacy.get("full_text")
        or quoted_tweet.get("text")
        or quoted_tweet.get("translation")
        or quoted_tweet.get("full_text")
        or quoted_tweet.get("content")
    )
    normalized_quote_text = _strip_trailing_tco_link(quoted_text).strip() if quoted_text else ""

    quote_author_name, quote_author_handle = extract_author(quoted_tweet)
    normalized_quote_author_name = quote_author_name or None
    normalized_quote_author_handle = quote_author_handle or None

    if not normalized_quote_text and not normalized_quote_author_name and not normalized_quote_author_handle:
        return None

    return normalized_quote_text or None, normalized_quote_author_name, normalized_quote_author_handle


def extract_post_url(tweet: dict[str, Any], status_id: str, handle: str | None, fallback: str) -> str:
    url = coerce_str(tweet.get("url") or tweet.get("tweet_url")) or ""
    if url:
        return url
    if handle:
        return f"https://x.com/{handle}/status/{status_id}"
    return fallback


def extract_media_sources(tweet: dict[str, Any]) -> list[MediaSource]:
    media = _extract_fxtwitter_media(tweet)

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

    for photo in iter_media_dicts(media.get("photos"), media.get("images")):
        if url := coerce_url(photo.get("url") or photo.get("src") or photo.get("source")):
            thumbnail_url, duration, width, height = _extract_media_metadata(photo)
            _add(MediaKind.PHOTO, url, thumbnail_url=thumbnail_url, duration=duration, width=width, height=height)

    for video in iter_media_dicts(media.get("videos"), media.get("video")):
        url = pick_video_url(video)
        if url:
            thumbnail_url, duration, width, height = _extract_media_metadata(video)
            _add(MediaKind.VIDEO, url, thumbnail_url=thumbnail_url, duration=duration, width=width, height=height)

    for item in iter_media_dicts(media.get("all")):
        kind = resolve_kind(item)
        url = pick_video_url(item) if kind == MediaKind.VIDEO else coerce_url(item.get("url") or item.get("src"))
        if not url:
            url = coerce_url(item.get("source"))
        if not url:
            continue

        thumbnail_url, duration, width, height = _extract_media_metadata(item)
        _add(kind, url, thumbnail_url=thumbnail_url, duration=duration, width=width, height=height)

    if not sources:
        for item in _extract_twitter_media_entries(tweet):
            kind = resolve_kind(item)
            thumbnail_url, _, width, height = _extract_media_metadata(item)

            if kind == MediaKind.VIDEO:
                video_info = dict_or_empty(item.get("video_info"))
                url = pick_video_url(video_info) or pick_video_url(item)
                if not url:
                    continue

                duration = _extract_twitter_video_duration_seconds(video_info)
                thumbnail_url = thumbnail_url or coerce_url(item.get("media_url_https") or item.get("media_url"))
                _add(MediaKind.VIDEO, url, thumbnail_url=thumbnail_url, duration=duration, width=width, height=height)
                continue

            photo_url = coerce_url(item.get("media_url_https") or item.get("media_url"))
            if not photo_url:
                continue

            _add(MediaKind.PHOTO, photo_url, width=width, height=height)

    if not sources:
        media_url = coerce_url(tweet.get("media_url") or tweet.get("media_url_https"))
        if media_url:
            _add(MediaKind.PHOTO, media_url)

    return sources


def pick_video_url(video: dict[str, Any]) -> str | None:
    variants = dict_list(video.get("variants"))
    if best_variant := pick_best_variant(variants):
        return best_variant

    direct_url = coerce_url(video.get("url") or video.get("src") or video.get("source"))
    if not direct_url:
        return None

    format_hint = video.get("format") or video.get("content_type")
    if looks_like_hls(direct_url, format_hint) or not looks_like_mp4(direct_url, format_hint):
        return None
    return direct_url


def pick_best_variant(variants: list[dict[str, Any]]) -> str | None:
    best_mp4_url: str | None = None
    best_mp4_bitrate = -1

    for variant in variants:
        if not isinstance(variant, dict):
            continue

        url = coerce_url(variant.get("url"))
        if not url:
            continue

        format_hint = variant.get("content_type") or variant.get("format")
        if looks_like_hls(url, format_hint) or not looks_like_mp4(url, format_hint):
            continue

        bitrate = coerce_int(variant.get("bitrate")) or -1
        if bitrate <= best_mp4_bitrate:
            continue

        best_mp4_bitrate = bitrate
        best_mp4_url = url

    return best_mp4_url


def looks_like_hls(url: str, format_hint: object) -> bool:
    lowered_url = url.lower()
    if ".m3u8" in lowered_url:
        return True

    parsed = urlparse(url)
    if parsed.path.lower().endswith(".m3u8"):
        return True

    if isinstance(format_hint, str):
        lowered_format = format_hint.lower()
        return "mpegurl" in lowered_format or "m3u8" in lowered_format

    return False


def looks_like_mp4(url: str, format_hint: object) -> bool:
    parsed = urlparse(url)
    if parsed.path.lower().endswith(".mp4"):
        return True

    if isinstance(format_hint, str):
        lowered_format = format_hint.lower()
        return "video/mp4" in lowered_format or lowered_format == "mp4"

    return False


def resolve_kind(item: dict[str, Any]) -> MediaKind:
    media_type = item.get("type")
    if isinstance(media_type, str) and media_type.lower() in _VIDEO_MEDIA_TYPES:
        return MediaKind.VIDEO
    return MediaKind.PHOTO


def extract_quoted_tweet(tweet: dict[str, Any]) -> dict[str, Any] | None:
    quoted_status_result = dict_or_empty(tweet.get("quoted_status_result"))
    if quoted_status_result:
        quoted_result = dict_or_empty(quoted_status_result.get("result"))
        if quoted_result:
            return quoted_result

    quote = dict_or_empty(tweet.get("quote"))
    if quote:
        return quote

    return None


def extract_legacy(tweet: dict[str, Any]) -> dict[str, Any]:
    legacy = dict_or_empty(tweet.get("legacy"))
    if legacy:
        return legacy

    nested_tweet = dict_or_empty(tweet.get("tweet"))
    return dict_or_empty(nested_tweet.get("legacy"))


def iter_media_dicts(*values: object) -> Iterator[dict[str, Any]]:
    for value in values:
        yield from dict_list(value)


def coerce_url(value: object) -> str | None:
    return coerce_str(value)


def _extract_media_metadata(item: dict[str, Any]) -> tuple[str | None, int | None, int | None, int | None]:
    original_info = dict_or_empty(item.get("original_info"))
    thumbnail_url = coerce_str(
        item.get("thumbnail_url")
        or item.get("thumb")
        or item.get("preview_image_url")
        or item.get("media_url_https")
        or item.get("media_url")
    )
    duration = coerce_int(item.get("duration"))
    width = coerce_int(item.get("width") or original_info.get("width"))
    height = coerce_int(item.get("height") or original_info.get("height"))
    return thumbnail_url, duration, width, height


def _extract_fxtwitter_media(tweet: dict[str, Any]) -> dict[str, Any]:
    media = dict_or_empty(tweet.get("media"))
    if media:
        return media

    quoted_tweet = extract_quoted_tweet(tweet)
    if not quoted_tweet:
        return {}

    return dict_or_empty(quoted_tweet.get("media"))


def _extract_twitter_media_entries(tweet: dict[str, Any]) -> list[dict[str, Any]]:
    legacy = extract_legacy(tweet)
    extended_entities = dict_or_empty(legacy.get("extended_entities"))
    media = dict_list(extended_entities.get("media"))
    if media:
        return media

    quoted_tweet = extract_quoted_tweet(tweet)
    if not quoted_tweet:
        return []

    quoted_legacy = extract_legacy(quoted_tweet)
    quoted_entities = dict_or_empty(quoted_legacy.get("extended_entities"))
    return dict_list(quoted_entities.get("media"))


def _extract_twitter_video_duration_seconds(video_info: dict[str, Any]) -> int | None:
    duration_ms = coerce_int(video_info.get("duration_millis"))
    if not duration_ms or duration_ms <= 0:
        return None
    return duration_ms // 1000


def _strip_trailing_tco_link(text: str) -> str:
    marker = "https://t.co/"
    index = text.find(marker)
    if index == -1:
        return text

    while index > 0 and text[index - 1] in {" ", "\n", "\r"}:
        index -= 1

    return text[:index]
