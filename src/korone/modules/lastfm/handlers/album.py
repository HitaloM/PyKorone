from __future__ import annotations

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
        lastfm_user = await get_lastfm_user_or_reply(self.event)
        if not lastfm_user:
            return

        track_data = await fetch_and_handle_recent_track(self.event, lastfm_user)
        if not track_data:
            return

        last_played, user_link = track_data

        if not last_played.album or not last_played.album.name:
            await self.event.reply(_("No album information found for the current track."))
            return

        last_fm = LastFMClient()
        album_info = await last_fm.get_album_info(last_played.artist.name, last_played.album.name, lastfm_user)

        entity_name = f"{last_played.artist.name} — {last_played.album.name}"
        playcount = getattr(album_info, "playcount", 0) if album_info else 0
        tags = format_tags(album_info) if album_info and getattr(album_info, "tags", None) else ""
        text = build_entity_response(
            user_link=user_link,
            now_playing=last_played.now_playing,
            emoji="💽",
            entity_name=entity_name,
            playcount=playcount,
            tags=tags,
        )

        image = await get_biggest_lastfm_image(last_played)
        await reply_with_optional_image(self.event, text, image)
