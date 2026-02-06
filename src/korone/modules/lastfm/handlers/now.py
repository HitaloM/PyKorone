from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from aiogram import flags

from korone.filters.cmd import CMDFilter
from korone.modules.lastfm.utils import (
    LastFMClient,
    build_entity_response,
    fetch_and_handle_recent_track,
    format_tags,
    get_biggest_lastfm_image,
    get_lastfm_user_or_reply,
    reply_with_optional_image,
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
        return (CMDFilter(("lfm", "lastfm", "lmu", "np")),)

    async def handle(self) -> None:
        lastfm_username = await get_lastfm_user_or_reply(self.event)
        if not lastfm_username:
            return

        track_data = await fetch_and_handle_recent_track(self.event, lastfm_username)
        if not track_data:
            return

        last_played, user_link = track_data
        last_fm = LastFMClient()

        track_info = None
        with contextlib.suppress(Exception):
            track_info = await last_fm.get_track_info(last_played.artist.name, last_played.name, lastfm_username)

        entity_name = f"{last_played.artist.name} — {last_played.name}"
        playcount = getattr(track_info, "playcount", 0) if track_info else 0
        tags = format_tags(track_info) if track_info and getattr(track_info, "tags", None) else ""
        text = build_entity_response(
            user_link=user_link,
            now_playing=last_played.now_playing,
            emoji="🎧",
            entity_name=entity_name,
            playcount=playcount,
            tags=tags,
        )

        image = await get_biggest_lastfm_image(last_played)
        await reply_with_optional_image(self.event, text, image)
