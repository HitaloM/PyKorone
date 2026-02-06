from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

from aiogram import flags

from korone.filters.cmd import CMDFilter
from korone.modules.lastfm.utils import (
    DeezerClient,
    DeezerError,
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


@flags.help(description=l_("Shows the artist info for your current track on Last.fm."))
@flags.disableable(name="lfmartist")
class LastFMArtistHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter(("lfmartist", "lart")),)

    async def handle(self) -> None:
        lastfm_username = await get_lastfm_user_or_reply(self.event)
        if not lastfm_username:
            return

        track_data = await fetch_and_handle_recent_track(self.event, lastfm_username)
        if not track_data:
            return

        last_played, user_link = track_data
        last_fm = LastFMClient()

        artist_info = None
        with suppress(Exception):
            artist_info = await last_fm.get_artist_info(last_played.artist.name, lastfm_username)

        entity_name = last_played.artist.name
        playcount = getattr(artist_info, "playcount", 0) if artist_info else 0
        tags = format_tags(artist_info) if artist_info and getattr(artist_info, "tags", None) else ""
        text = build_entity_response(
            user_link=user_link,
            now_playing=last_played.now_playing,
            emoji="👨‍🎤",
            entity_name=entity_name,
            playcount=playcount,
            tags=tags,
        )

        with suppress(DeezerError):
            deezer = DeezerClient()
            artist = await deezer.get_artist(last_played.artist.name)
            if artist and (picture := artist.picture_xl or artist.picture_big):
                await self.event.reply_photo(photo=picture, caption=text)
                return

        image = await get_biggest_lastfm_image(last_played)
        await reply_with_optional_image(self.event, text, image)
