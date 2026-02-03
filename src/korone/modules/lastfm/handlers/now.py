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
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


@flags.help(description=l_("Shows your now playing track from Last.fm."))
@flags.disableable(name="lastfm")
class LastFMNowHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter(("lfm", "lastfm", "lmu")),)

    async def handle(self) -> None:
        last_fm_user = await get_lastfm_user_or_reply(self.event)
        if not last_fm_user:
            return

        track_data = await fetch_and_handle_recent_track(self.event, last_fm_user)
        if not track_data:
            return

        last_played, user_link = track_data
        last_fm = LastFMClient()
        track_info = await get_entity_info(last_fm, last_played, last_fm_user, "track")

        await send_entity_response(
            self.event, last_played, user_link, track_info, "🎧", f"{last_played.artist.name} — {last_played.name}"
        )
