# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command
from korone.handlers.abstract import MessageHandler
from korone.modules.lastfm.database import get_lastfm_user
from korone.modules.lastfm.utils import (
    DeezerClient,
    DeezerError,
    LastFMClient,
    LastFMError,
    format_tags,
    get_time_elapsed_str,
    name_with_link,
)
from korone.utils.i18n import gettext as _


class LastFMPlayingArtistHandler(MessageHandler):
    @staticmethod
    @router.message(Command(commands=["lfmartist", "lart"]))
    async def handle(client: Client, message: Message) -> None:
        last_fm_user = await get_lastfm_user(message.from_user.id)
        if not last_fm_user:
            await message.reply(
                _(
                    "You need to set your LastFM username first! "
                    "Example: <code>/setlfm username</code>."
                )
            )
            return

        last_fm = LastFMClient()

        try:
            last_played = (await last_fm.get_recent_tracks(last_fm_user, limit=1))[0]
            artist_info = await last_fm.get_artist_info(last_played.artist.name, last_fm_user)
        except LastFMError as e:
            if "user not found" in e.message.lower():
                await message.reply(_("Your LastFM username was not found! Try setting it again."))
                return
            raise
        except IndexError:
            await message.reply(_("No recent tracks found for your LastFM account."))
            return

        user_link = name_with_link(name=str(message.from_user.first_name), username=last_fm_user)

        if last_played.now_playing:
            text = _("{user}'s is listening to:\n").format(user=user_link)
        else:
            text = _("{user}'s was listening to:\n").format(user=user_link)

        text += "👨‍🎤 <b>{artist_name}</b>{time}{plays}".format(
            artist_name=last_played.artist.name,
            time="" if last_played.now_playing else get_time_elapsed_str(last_played),
            plays=_(" ∙ <code>{artist_playcount} plays</code>").format(
                artist_playcount=artist_info.playcount
            )
            if artist_info.playcount > 0
            else "",
        )

        if artist_info.tags:
            text += f"\n\n{format_tags(artist_info)}"

        deezer = DeezerClient()
        try:
            artist = await deezer.get_artist(last_played.artist.name)
        except DeezerError:
            artist = None

        if artist and (picture := artist.picture_xl or artist.picture_big):
            await message.reply_photo(photo=picture, caption=text)
            return

        await message.reply(text, disable_web_page_preview=True)
