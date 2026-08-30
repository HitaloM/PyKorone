import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from korone.modules.medias.models import MediaKind, MediaSource

from . import parser

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable


@dataclass(frozen=True, slots=True)
class _Variant:
    path: str
    bandwidth: int
    width: int | None
    height: int | None
    audio_group: str | None


async def resolve_streams(
    hls_url: str | None, fetch_text: Callable[[str], Awaitable[str | None]]
) -> MediaSource | None:
    if not hls_url or not (master_playlist := await fetch_text(hls_url)):
        return None

    variant, audio_groups = _select_variant(master_playlist)
    if variant is None:
        return None

    variant_playlist_url = parser.normalize_media_url(hls_url, variant.path)
    if not variant_playlist_url or not (variant_playlist := await fetch_text(variant_playlist_url)):
        return None

    video_path = extract_media_path(variant_playlist)
    if not video_path:
        return None

    video_url = parser.normalize_media_url(variant_playlist_url, video_path)
    if not video_url:
        return None

    audio_url = await _resolve_audio_url(hls_url, variant.audio_group, audio_groups, fetch_text)
    return MediaSource(
        kind=MediaKind.VIDEO,
        url=video_url,
        audio_url=audio_url,
        width=variant.width,
        height=variant.height,
        duration=parse_segment_duration(variant_playlist),
    )


def _select_variant(master_playlist: str) -> tuple[_Variant | None, dict[str, str]]:
    audio_groups: dict[str, str] = {}
    variants: list[_Variant] = []
    stream_info: str | None = None

    for raw_line in master_playlist.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#EXT-X-MEDIA:"):
            media_type = parse_stream_text(line, "TYPE")
            group_id = parse_stream_text(line, "GROUP-ID")
            uri = parse_stream_text(line, "URI")
            if media_type == "AUDIO" and group_id and uri:
                audio_groups[group_id] = uri
            continue
        if line.startswith("#EXT-X-STREAM-INF:"):
            stream_info = line
            continue
        if line.startswith("#") or stream_info is None:
            continue

        width, height = parse_stream_resolution(stream_info)
        variants.append(
            _Variant(
                path=line,
                bandwidth=parse_stream_int(stream_info, "BANDWIDTH"),
                width=width,
                height=height,
                audio_group=parse_stream_text(stream_info, "AUDIO"),
            )
        )
        stream_info = None

    return (max(variants, key=lambda variant: variant.bandwidth) if variants else None), audio_groups


async def _resolve_audio_url(
    master_url: str,
    preferred_group: str | None,
    audio_groups: dict[str, str],
    fetch_text: Callable[[str], Awaitable[str | None]],
) -> str | None:
    candidates: list[str] = []
    if preferred_group and (preferred_uri := audio_groups.get(preferred_group)):
        candidates.append(preferred_uri)
    candidates.extend(uri for uri in audio_groups.values() if uri not in candidates)

    for uri in candidates:
        playlist_url = parser.normalize_media_url(master_url, uri)
        if not playlist_url or not (playlist := await fetch_text(playlist_url)):
            continue
        if (media_path := extract_media_path(playlist)) and (
            media_url := parser.normalize_media_url(playlist_url, media_path)
        ):
            return media_url
    return None


def extract_media_path(playlist: str) -> str | None:
    for raw_line in playlist.splitlines():
        line = raw_line.strip()
        if line and not line.startswith("#"):
            return line
    return None


def parse_stream_text(stream_info: str, key: str) -> str | None:
    match = re.search(rf'{re.escape(key)}=(?:"([^"]*)"|([^,\s]+))', stream_info)
    return (match.group(1) or match.group(2)) if match else None


def parse_stream_int(stream_info: str, key: str) -> int:
    match = re.search(rf"{re.escape(key)}=(\d+)", stream_info)
    return int(match.group(1)) if match else -1


def parse_stream_resolution(stream_info: str) -> tuple[int | None, int | None]:
    match = re.search(r"RESOLUTION=(\d+)x(\d+)", stream_info)
    return (int(match.group(1)), int(match.group(2))) if match else (None, None)


def parse_segment_duration(playlist: str) -> int | None:
    durations: list[float] = []
    for raw_line in playlist.splitlines():
        match = re.match(r"(?i)#EXTINF:([0-9]+(?:\.[0-9]+)?)", raw_line.strip())
        if not match:
            continue
        duration = float(match.group(1))
        if duration > 0:
            durations.append(duration)

    if not durations:
        return None
    return max(1, int(sum(durations) + 0.5))
