from __future__ import annotations

import math
import mimetypes
import re
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from stfu_tg import Code, Doc, KeyValue, Title

from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from .types import HifiTrack, HifiTrackStream

RESULTS_PER_PAGE = 8
MAX_TRACK_BUTTON_TEXT_LENGTH = 56
MAX_FILENAME_LENGTH = 120
FILENAME_SANITIZER_PATTERN = re.compile(r"[^A-Za-z0-9 _\-.()]+")
DEFAULT_AUDIO_EXTENSION = ".m4a"
TIDAL_COVER_BASE_URL = "https://resources.tidal.com/images"


def _truncate_text(text: str, max_length: int = MAX_TRACK_BUTTON_TEXT_LENGTH) -> str:
    if len(text) <= max_length:
        return text

    return f"{text[: max_length - 1]}…"


def _track_display_name(track: HifiTrack) -> str:
    if track.artist:
        return f"{track.artist} - {track.title}"
    return track.title


def get_last_page(total_count: int) -> int:
    if total_count <= 0:
        return 1
    return max(1, math.ceil(total_count / RESULTS_PER_PAGE))


def clamp_page(page: int, total_count: int) -> int:
    return min(max(1, page), get_last_page(total_count))


def format_track_button(index: int, track: HifiTrack) -> str:
    return _truncate_text(f"{index + 1}. {_track_display_name(track)}")


def build_search_results_text(query: str, total_count: int, page: int) -> str:
    current_page = clamp_page(page, total_count)
    last_page = get_last_page(total_count)

    doc = Doc(Title(_("HiFi search")), KeyValue(_("Query"), query), KeyValue(_("Found tracks"), Code(str(total_count))))

    if total_count > 0:
        doc += KeyValue(_("Page"), Code(f"{current_page}/{last_page}"))
        doc += _("Select a track below to preview and download it.")

    return str(doc)


def format_duration(seconds: int | None) -> str:
    if seconds is None:
        return _("Unknown")

    minutes, sec = divmod(max(0, seconds), 60)
    hours, min_ = divmod(minutes, 60)

    if hours:
        return f"{hours}:{min_:02}:{sec:02}"

    return f"{min_}:{sec:02}"


def build_track_preview_text(track: HifiTrack) -> str:
    quality = track.audio_quality or _("Unknown")

    doc = Doc(Title(_("Track preview")), KeyValue(_("Track"), track.title), KeyValue(_("Artist"), track.artist))

    if track.album:
        doc += KeyValue(_("Album"), track.album)

    doc += KeyValue(_("Duration"), Code(format_duration(track.duration)))
    doc += KeyValue(_("Quality"), Code(quality))

    if track.explicit:
        doc += _("Explicit content.")

    doc += _("Use the buttons below to go back or download this track.")

    return str(doc)


def build_track_caption(track: HifiTrack, stream: HifiTrackStream) -> str:
    quality = stream.audio_quality or track.audio_quality or stream.requested_quality

    doc = Doc(Title(_("Track sent")), KeyValue(_("Track"), track.title), KeyValue(_("Artist"), track.artist))

    if track.album:
        doc += KeyValue(_("Album"), track.album)

    doc += KeyValue(_("Quality"), Code(quality))

    if track.explicit:
        doc += _("Explicit content.")

    return str(doc)


def build_album_cover_url(track: HifiTrack) -> str | None:
    if not track.album_cover_id:
        return None

    slug = track.album_cover_id.replace("-", "/")
    return f"{TIDAL_COVER_BASE_URL}/{slug}/750x750.jpg"


def _sanitize_filename_part(value: str, fallback: str) -> str:
    cleaned = FILENAME_SANITIZER_PATTERN.sub("_", value).strip(" ._")
    if cleaned:
        return cleaned
    return fallback


def _extension_from_content_type(content_type: str) -> str | None:
    normalized = content_type.split(";", maxsplit=1)[0].strip().lower()
    if not normalized:
        return None

    extension = mimetypes.guess_extension(normalized)
    if extension == ".mp4":
        return ".m4a"

    return extension


def _guess_audio_extension(stream: HifiTrackStream, content_type: str | None) -> str:
    path = Path(urlparse(stream.url).path)
    if path.suffix:
        return path.suffix.lower()

    if content_type and (extension := _extension_from_content_type(content_type)):
        return extension

    if stream.mime_type in {"audio/flac", "audio/x-flac"}:
        return ".flac"

    if stream.mime_type in {"audio/mp4", "audio/aac"}:
        return ".m4a"

    return DEFAULT_AUDIO_EXTENSION


def build_track_filename(track: HifiTrack, stream: HifiTrackStream, content_type: str | None) -> str:
    artist = _sanitize_filename_part(track.artist, "artist")
    title = _sanitize_filename_part(track.title, f"track-{track.id}")
    extension = _guess_audio_extension(stream, content_type)

    filename = f"{artist} - {title}{extension}"
    if len(filename) <= MAX_FILENAME_LENGTH:
        return filename

    max_title_length = max(8, MAX_FILENAME_LENGTH - len(artist) - len(extension) - 3)
    trimmed_title = title[:max_title_length].rstrip(" ._") or f"track-{track.id}"
    return f"{artist} - {trimmed_title}{extension}"
