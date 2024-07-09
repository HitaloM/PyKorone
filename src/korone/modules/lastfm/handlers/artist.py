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
    @router.message(Command(commands=["lfmar", "art", "artist"]))
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
            artist_info = await last_fm.get_artist_info(last_played.artist, last_fm_user)
        except LastFMError as e:
            error_message = str(e)
            if error_message == "User not found":
                await message.reply(_("Your LastFM username was not found! Try setting it again."))
            else:
                await message.reply(
                    _(
                        "An error occurred while fetching your LastFM data!\nError: <i>{error}</i>"
                    ).format(error=error_message)
                )
            return

        user_link = name_with_link(name=str(message.from_user.first_name), username=last_fm_user)

        if last_played.now_playing:
            text = _("{user}'s is listening to:\n").format(user=user_link)
        else:
            text = _("{user}'s was listening to:\n").format(user=user_link)

        text += "<b>{artist_name}</b>{loved}{time}{plays}".format(
            artist_name=artist_info.name,
            loved=_(", ❤️ loved") if artist_info.loved else "",
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
            artist = await deezer.get_artist(artist_info.name)
        except DeezerError:
            artist = None

        if artist:
            await message.reply_photo(photo=artist.image.url, caption=text)
            return

        await message.reply(text, disable_web_page_preview=True)
