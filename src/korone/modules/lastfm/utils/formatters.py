from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from urllib.parse import quote_plus

from stfu_tg import Bold, HList, Italic, Template, Url

from korone.utils.i18n import gettext as _

from .errors import LastFMAPIError, LastFMConfigurationError, LastFMRequestError

if TYPE_CHECKING:
    from collections.abc import Sequence

    from .errors import LastFMError
    from .types import LastFMAlbumInfo, LastFMArtistInfo, LastFMRecentTrack, LastFMTrackInfo

TAG_SANITIZER_RE = re.compile(r"[^a-z0-9]+")


def _build_profile_link(username: str) -> Url:
    return Url(username, f"https://www.last.fm/user/{quote_plus(username)}")


def _format_elapsed_time(played_at: int | None) -> str | None:
    if played_at is None:
        return None

    played_at_datetime = datetime.fromtimestamp(played_at, tz=UTC)
    elapsed = datetime.now(tz=UTC) - played_at_datetime

    if elapsed.days > 0:
        return str(Template(_(", {days} day(s) ago"), days=elapsed.days))

    elapsed_seconds = int(elapsed.total_seconds())
    hours, remainder = divmod(max(elapsed_seconds, 0), 3600)
    if hours > 0:
        return str(Template(_(", {hours} hour(s) ago"), hours=hours))

    minutes, _seconds = divmod(remainder, 60)
    if minutes > 0:
        return str(Template(_(", {minutes} minute(s) ago"), minutes=minutes))

    return _(", just now")


def _build_tags_text(tags: tuple[str, ...]) -> str | None:
    parsed_tags: list[str] = []
    seen: set[str] = set()

    for raw_tag in tags:
        normalized = TAG_SANITIZER_RE.sub("_", raw_tag.strip().lower()).strip("_")
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        parsed_tags.append(f"#{normalized}")

    if not parsed_tags:
        return None

    return str(HList(*parsed_tags, divider=" "))


def _build_spotify_search_url(*parts: str) -> str:
    query = quote_plus(" - ".join(part for part in parts if part))
    return f"https://open.spotify.com/search/{query}"


def _build_inline_text(*parts: str | Bold | Italic | Template | Url | None) -> str:
    return str(HList(*(part for part in parts if part), divider=""))


def _build_playcount_text(playcount: int) -> str | None:
    if playcount <= 0:
        return None

    return str(Template(_(", {plays} plays"), plays=playcount))


def _build_track_line(track: LastFMRecentTrack, *, user_playcount: int = 0) -> str:
    album_text = Template(_(", [{album}]"), album=track.album) if track.album else None
    elapsed_text = None if track.now_playing else _format_elapsed_time(track.played_at)
    loved_text = _(", loved") if track.loved else None

    return _build_inline_text(
        "🎧 ",
        Italic(track.artist),
        " — ",
        Url(Bold(track.name), _build_spotify_search_url(track.artist, track.name)),
        album_text,
        elapsed_text,
        loved_text,
        _build_playcount_text(user_playcount),
    )


def _build_album_line(track: LastFMRecentTrack, *, album_name: str, album_artist: str, playcount: int) -> str:
    elapsed_text = None if track.now_playing else _format_elapsed_time(track.played_at)

    return _build_inline_text(
        "💽 ",
        Italic(album_artist),
        " — ",
        Url(Bold(album_name), _build_spotify_search_url(album_artist, album_name)),
        elapsed_text,
        _build_playcount_text(playcount),
    )


def _build_artist_line(track: LastFMRecentTrack, *, artist_name: str, playcount: int) -> str:
    elapsed_text = None if track.now_playing else _format_elapsed_time(track.played_at)

    return _build_inline_text(
        "🎙️ ",
        Url(Bold(artist_name), _build_spotify_search_url(artist_name)),
        elapsed_text,
        _build_playcount_text(playcount),
    )


def _append_tags_block(lines: list[str], tags: tuple[str, ...]) -> None:
    tags_text = _build_tags_text(tags)
    if not tags_text:
        return

    lines.extend(("", tags_text, ""))


def format_status(username: str, tracks: Sequence[LastFMRecentTrack], track_info: LastFMTrackInfo | None) -> str:
    if not tracks:
        return _("No scrobbles found for this Last.fm user.")

    first_track = tracks[0]
    lines = [
        str(
            Template(
                _("{user} is now listening to") if first_track.now_playing else _("{user} was listening to"),
                user=_build_profile_link(username),
            )
        )
    ]

    for index, track in enumerate(tracks):
        user_playcount = track_info.user_playcount if index == 0 and track_info else 0
        lines.append(_build_track_line(track, user_playcount=user_playcount))

        if index == 0 and track_info:
            _append_tags_block(lines, track_info.tags)

    return "\n".join(lines)


def format_album_status(username: str, track: LastFMRecentTrack, album_info: LastFMAlbumInfo | None) -> str:
    album_name = album_info.name if album_info else (track.album or _("Unknown album"))
    album_artist = album_info.artist if album_info else track.artist

    lines = [
        str(
            Template(
                _("{user} is now listening to album") if track.now_playing else _("{user} was listening to album"),
                user=_build_profile_link(username),
            )
        ),
        _build_album_line(
            track,
            album_name=album_name,
            album_artist=album_artist,
            playcount=album_info.user_playcount if album_info else 0,
        ),
    ]

    if album_info:
        tags_text = _build_tags_text(album_info.tags)
        if tags_text:
            lines.extend(("", tags_text))

    return "\n".join(lines)


def format_artist_status(username: str, track: LastFMRecentTrack, artist_info: LastFMArtistInfo | None) -> str:
    artist_name = artist_info.name if artist_info else track.artist

    lines = [
        str(
            Template(
                _("{user} is now listening to artist") if track.now_playing else _("{user} was listening to artist"),
                user=_build_profile_link(username),
            )
        ),
        _build_artist_line(track, artist_name=artist_name, playcount=artist_info.user_playcount if artist_info else 0),
    ]

    if artist_info:
        tags_text = _build_tags_text(artist_info.tags)
        if tags_text:
            lines.extend(("", tags_text))

    return "\n".join(lines)


def format_lastfm_error(error: LastFMError) -> str:
    if isinstance(error, LastFMConfigurationError):
        return _("Last.fm API key is not configured on this bot.")

    if isinstance(error, LastFMRequestError):
        return _("Could not reach Last.fm right now. Please try again later.")

    if isinstance(error, LastFMAPIError):
        if error.error_code == 6:
            return _("Last.fm user not found.")
        if error.error_code == 17:
            return _("This Last.fm profile is private.")
        if error.error_code == 29:
            return _("Last.fm rate limit exceeded. Please try again in a moment.")
        return str(error)

    return _("Unexpected Last.fm error.")
