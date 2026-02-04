from __future__ import annotations

import html
from typing import TYPE_CHECKING

from aiogram import flags

from korone.filters.cmd import CMDFilter
from korone.modules.lastfm.utils import (
    LastFMClient,
    LastFMError,
    get_lastfm_user_or_reply,
    get_time_elapsed_str,
    get_user_link,
    handle_lastfm_error,
)
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType

    from korone.modules.lastfm.utils import LastFMTrack


@flags.help(description=l_("Shows your recent tracks from Last.fm."))
@flags.disableable(name="lfmrecent")
class LastFMRecentHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter("lfmrecent"),)

    @staticmethod
    def format_recent_tracks(recent_tracks: list[LastFMTrack], user_link: str) -> str:
        last_played = recent_tracks[0]
        played_tracks = recent_tracks[1:6] if last_played.now_playing else recent_tracks[:5]

        formatted_tracks: list[str] = []
        if last_played.now_playing:
            formatted_tracks.extend([
                _("{user} is listening to:\n").format(user=user_link)
                + f"🎧 <i>{html.escape(last_played.artist.name)}</i> — "
                f"<b>{html.escape(last_played.name)}</b>",
                _("\nLast 5 plays:"),
            ])
        else:
            formatted_tracks.append(_("{user} was listening to:\n").format(user=user_link))

        formatted_tracks.extend(
            f"🎧 <i>{html.escape(track.artist.name)}</i> — "
            f"<b>{html.escape(track.name)}</b>"
            f"{get_time_elapsed_str(track)}"
            for track in played_tracks
        )

        return "\n".join(formatted_tracks)

    async def handle(self) -> None:
        last_fm_user = await get_lastfm_user_or_reply(self.event)
        if not last_fm_user:
            return

        last_fm = LastFMClient()
        try:
            recent_tracks = await last_fm.get_recent_tracks(last_fm_user, limit=6)
        except LastFMError as exc:
            await handle_lastfm_error(self.event, exc)
            return

        if not recent_tracks:
            await self.event.reply(_("No recent tracks found."))
            return

        user_link = get_user_link(self.event, last_fm_user)
        formatted_response = self.format_recent_tracks(recent_tracks, user_link)
        await self.event.reply(formatted_response, disable_web_page_preview=True)
