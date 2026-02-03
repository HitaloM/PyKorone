from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import flags

from korone.filters.cmd import CMDFilter
from korone.modules.lastfm.utils import (
    LastFMClient,
    fetch_and_handle_recent_track,
    get_entity_info,
    get_lastfm_user_or_reply,
    send_entity_response,
)
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


@flags.help(description=l_("Shows the album info for your current track on Last.fm."))
@flags.disableable(name="lfmalbum")
class LastFMAlbumHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter(("lfmalbum", "lalb")),)

    async def handle(self) -> None:
        last_fm_user = await get_lastfm_user_or_reply(self.event)
        if not last_fm_user:
            return

        track_data = await fetch_and_handle_recent_track(self.event, last_fm_user)
        if not track_data:
            return

        last_played, user_link = track_data

        if not last_played.album or not last_played.album.name:
            await self.event.reply(_("No album information found for the current track."))
            return

        last_fm = LastFMClient()
        album_info = await get_entity_info(last_fm, last_played, last_fm_user, "album")

        await send_entity_response(
            self.event,
            last_played,
            user_link,
            album_info,
            "💽",
            f"{last_played.artist.name} — {last_played.album.name}",
        )
