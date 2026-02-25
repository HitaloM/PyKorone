from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from urllib.parse import quote_plus

from stfu_tg import Bold, Italic, Template, Url

from korone.utils.i18n import gettext as _

from .errors import LastFMAPIError, LastFMConfigurationError, LastFMRequestError

if TYPE_CHECKING:
    from collections.abc import Sequence

    from .errors import LastFMError
    from .types import LastFMAlbumInfo, LastFMArtistInfo, LastFMRecentTrack, LastFMTrackInfo

TAG_SANITIZER_RE = re.compile(r"[^a-z0-9]+")


def _format_elapsed_time(played_at: int | None) -> str:
    if played_at is None:
        return ""

    played_at_datetime = datetime.fromtimestamp(played_at, tz=UTC)
    elapsed = datetime.now(tz=UTC) - played_at_datetime

    if elapsed.days > 0:
        return Template(_(", {days} day(s) ago"), days=elapsed.days).to_html()

    elapsed_seconds = int(elapsed.total_seconds())
    hours, remainder = divmod(max(elapsed_seconds, 0), 3600)
    if hours > 0:
        return Template(_(", {hours} hour(s) ago"), hours=hours).to_html()

    minutes, _seconds = divmod(remainder, 60)
    if minutes > 0:
        return Template(_(", {minutes} minute(s) ago"), minutes=minutes).to_html()

    return _(", just now")


def _format_tags(tags: tuple[str, ...]) -> str:
    parsed_tags: list[str] = []
    seen: set[str] = set()

    for raw_tag in tags:
        normalized = TAG_SANITIZER_RE.sub("_", raw_tag.strip().lower()).strip("_")
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        parsed_tags.append(f"#{normalized}")

    return " ".join(parsed_tags)


def _build_spotify_search_url(artist: str, track: str) -> str:
    query = quote_plus(f"{artist} - {track}")
    return f"https://open.spotify.com/search/{query}"


def format_status(username: str, tracks: Sequence[LastFMRecentTrack], track_info: LastFMTrackInfo | None) -> str:
    if not tracks:
        return _("No scrobbles found for this Last.fm user.")

    first_track = tracks[0]
    profile_url = f"https://www.last.fm/user/{quote_plus(username)}"

    header = Template(
        _("{user} is now listening to") if first_track.now_playing else _("{user} was listening to"),
        user=Url(username, profile_url),
    ).to_html()

    tags_text = _format_tags(track_info.tags) if track_info else ""

    lines: list[str] = []
    for index, track in enumerate(tracks):
        spotify_search_url = _build_spotify_search_url(track.artist, track.name)
        album_text = Template(_(", [{album}]"), album=track.album).to_html() if track.album else ""
        elapsed = "" if track.now_playing else _format_elapsed_time(track.played_at)
        loved_text = _(", loved") if track.loved else ""

        user_playcount = track_info.user_playcount if index == 0 and track_info else 0
        playcount_text = Template(_(", {plays} plays"), plays=user_playcount).to_html() if user_playcount > 0 else ""
        tags_block = f"\n\n{tags_text}\n" if index == 0 and tags_text else ""

        lines.append(
            Template(
                "🎧 {artist} — {track}{album}{elapsed}{loved}{playcount}{tags}",
                artist=Italic(track.artist),
                track=Url(Bold(track.name), spotify_search_url),
                album=album_text,
                elapsed=elapsed,
                loved=loved_text,
                playcount=playcount_text,
                tags=tags_block,
            ).to_html()
        )

    return f"{header}\n" + "\n".join(lines)


def format_album_status(username: str, track: LastFMRecentTrack, album_info: LastFMAlbumInfo | None) -> str:
    profile_url = f"https://www.last.fm/user/{quote_plus(username)}"
    header = Template(
        _("{user} is now listening to album") if track.now_playing else _("{user} was listening to album"),
        user=Url(username, profile_url),
    ).to_html()

    album_name = album_info.name if album_info else (track.album or _("Unknown album"))
    album_artist = album_info.artist if album_info else track.artist
    spotify_search_url = _build_spotify_search_url(album_artist, album_name)

    elapsed = "" if track.now_playing else _format_elapsed_time(track.played_at)
    playcount = album_info.user_playcount if album_info else 0
    playcount_text = Template(_(", {plays} plays"), plays=playcount).to_html() if playcount > 0 else ""

    tags_text = _format_tags(album_info.tags) if album_info else ""
    tags_suffix = f"\n\n{tags_text}" if tags_text else ""

    line = Template(
        "💽 {artist} — {album}{elapsed}{playcount}",
        artist=Italic(album_artist),
        album=Url(Bold(album_name), spotify_search_url),
        elapsed=elapsed,
        playcount=playcount_text,
    ).to_html()

    return f"{header}\n{line}{tags_suffix}"


def format_artist_status(username: str, track: LastFMRecentTrack, artist_info: LastFMArtistInfo | None) -> str:
    profile_url = f"https://www.last.fm/user/{quote_plus(username)}"
    header = Template(
        _("{user} is now listening to artist") if track.now_playing else _("{user} was listening to artist"),
        user=Url(username, profile_url),
    ).to_html()

    artist_name = artist_info.name if artist_info else track.artist
    spotify_search_url = quote_plus(artist_name)
    artist_url = f"https://open.spotify.com/search/{spotify_search_url}"

    elapsed = "" if track.now_playing else _format_elapsed_time(track.played_at)
    playcount = artist_info.user_playcount if artist_info else 0
    playcount_text = Template(_(", {plays} plays"), plays=playcount).to_html() if playcount > 0 else ""

    tags_text = _format_tags(artist_info.tags) if artist_info else ""
    tags_suffix = f"\n\n{tags_text}" if tags_text else ""

    line = Template(
        "🎙️ {artist}{elapsed}{playcount}",
        artist=Url(Bold(artist_name), artist_url),
        elapsed=elapsed,
        playcount=playcount_text,
    ).to_html()

    return f"{header}\n{line}{tags_suffix}"


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
