import asyncio
from typing import TYPE_CHECKING

from aiogram.enums import ParseMode
from aiogram.types import (
    InlineQueryResultArticle,
    InlineQueryResultsButton,
    InputTextMessageContent,
    LinkPreviewOptions,
)

from korone.db.repositories.lastfm import LastFMRepository
from korone.modules.metadata import InlineQueryContribution
from korone.utils.i18n import gettext as _

from .callbacks import LastFMMode
from .handlers.album import LastFMAlbumPayload, LastFMAlbumView
from .handlers.artist import LastFMArtistPayload, LastFMArtistView
from .handlers.base import LASTFM_SET_START_PAYLOAD, LastFMHandlerSupport, LastFMUserContext
from .handlers.lfm import LastFMStatusPayload, LastFMStatusView
from .utils import LastFMClient, LastFMError, format_lastfm_error

if TYPE_CHECKING:
    from collections.abc import Awaitable

    from aiogram.types import InlineQuery

    from .utils import LastFMRecentTrack


async def _capture_lastfm_error[T](awaitable: Awaitable[T]) -> T | LastFMError:
    try:
        return await awaitable
    except LastFMError as exc:
        return exc


def _message_content(text: str, image_url: str | None = None) -> InputTextMessageContent:
    preview_options = None
    if image_url:
        preview_options = LinkPreviewOptions(
            is_disabled=False, url=image_url, prefer_large_media=True, show_above_text=False
        )
    return InputTextMessageContent(message_text=text, parse_mode=ParseMode.HTML, link_preview_options=preview_options)


def _article(
    *, result_id: str, title: str, description: str, text: str, image_url: str | None = None
) -> InlineQueryResultArticle:
    return InlineQueryResultArticle(
        id=result_id,
        title=title,
        description=description,
        thumbnail_url=image_url,
        input_message_content=_message_content(text, image_url),
    )


def _informational_contribution(*, title: str, text: str) -> InlineQueryContribution:
    return InlineQueryContribution(
        results=(_article(result_id="information", title=title, description=text, text=text),)
    )


def _track_result(payload: LastFMStatusPayload, track: LastFMRecentTrack) -> InlineQueryResultArticle:
    image_url = LastFMHandlerSupport.resolve_image_url(payload.image_url)
    return _article(
        result_id="track",
        title=_("Current track"),
        description=f"{track.artist} — {track.name}",
        text=payload.text,
        image_url=image_url,
    )


def _album_result(payload: LastFMAlbumPayload | None, track: LastFMRecentTrack) -> InlineQueryResultArticle:
    if payload is None:
        empty_text = LastFMAlbumView.empty_state_text()
        return _article(result_id="album", title=_("Current album"), description=empty_text, text=empty_text)

    image_url = LastFMHandlerSupport.resolve_image_url(payload.image_url)
    album_name = payload.album_info.name if payload.album_info else track.album
    return _article(
        result_id="album",
        title=_("Current album"),
        description=f"{track.artist} — {album_name}",
        text=payload.text,
        image_url=image_url,
    )


def _artist_result(payload: LastFMArtistPayload, track: LastFMRecentTrack) -> InlineQueryResultArticle:
    image_url = LastFMHandlerSupport.resolve_image_url(payload.image_url)
    artist_name = payload.artist_info.name if payload.artist_info else track.artist
    return _article(
        result_id="artist", title=_("Current artist"), description=artist_name, text=payload.text, image_url=image_url
    )


async def provide_lastfm_inline(query: InlineQuery) -> InlineQueryContribution:
    username = await LastFMRepository.get_username(query.from_user.id)
    if not username:
        return InlineQueryContribution(
            button=InlineQueryResultsButton(text=_("Set up Last.fm"), start_parameter=LASTFM_SET_START_PAYLOAD)
        )

    user = LastFMUserContext(
        username=username, display_name=query.from_user.first_name, telegram_user_id=query.from_user.id
    )
    client = LastFMClient()
    try:
        recent_tracks = await client.get_recent_tracks(username=username, limit=1)
    except LastFMError as exc:
        return _informational_contribution(title=_("Last.fm unavailable"), text=format_lastfm_error(exc))

    if not recent_tracks:
        return _informational_contribution(title=_("No recent scrobbles"), text=LastFMStatusView.empty_state_text())

    track = recent_tracks[0]
    async with asyncio.TaskGroup() as task_group:
        status_task = task_group.create_task(
            _capture_lastfm_error(
                LastFMStatusView.build_status_payload_from_tracks(
                    user=user, mode=LastFMMode.COMPACT, tracks=recent_tracks
                )
            )
        )
        album_task = task_group.create_task(
            _capture_lastfm_error(LastFMAlbumView.build_payload_from_track(user=user, track=track))
        )
        artist_task = task_group.create_task(
            _capture_lastfm_error(LastFMArtistView.build_payload_from_track(user=user, track=track))
        )

    status_payload = status_task.result()
    album_payload = album_task.result()
    artist_payload = artist_task.result()
    if isinstance(status_payload, LastFMError):
        return _informational_contribution(title=_("Last.fm unavailable"), text=format_lastfm_error(status_payload))
    if isinstance(album_payload, LastFMError):
        return _informational_contribution(title=_("Last.fm unavailable"), text=format_lastfm_error(album_payload))
    if isinstance(artist_payload, LastFMError):
        return _informational_contribution(title=_("Last.fm unavailable"), text=format_lastfm_error(artist_payload))

    if status_payload is None:
        return _informational_contribution(title=_("No recent scrobbles"), text=LastFMStatusView.empty_state_text())

    return InlineQueryContribution(
        results=(
            _track_result(status_payload, track),
            _album_result(album_payload, track),
            _artist_result(artist_payload, track),
        )
    )
