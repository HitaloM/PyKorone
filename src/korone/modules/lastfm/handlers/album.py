# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.handlers.abstract.message_handler import MessageHandler
from korone.modules.lastfm.database import get_lastfm_user
from korone.modules.lastfm.utils import (
    LastFMClient,
    LastFMError,
    format_tags,
    get_biggest_lastfm_image,
    get_time_elapsed_str,
    name_with_link,
)
from korone.modules.utils.filters import Command
from korone.utils.i18n import gettext as _


class LastFMPlayingAlbumHandler(MessageHandler):
    @staticmethod
    @router.message(Command(commands=["lfmal", "alb", "album"]))
    async def handle(client: Client, message: Message) -> None:
        last_fm_user = await get_lastfm_user(message.from_user.id)
        if not last_fm_user:
            await message.reply(_("You need to set your LastFM username first!"))
            return

        last_fm = LastFMClient()

        try:
            last_played = (await last_fm.get_recent_tracks(last_fm_user, limit=1))[0]
            album_info = await last_fm.get_album_info(
                last_played.artist, last_played.album, last_fm_user
            )
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

        text += "💽 <i>{album_artist}</i> — <b>{album_name}</b>{loved}{time}{plays}".format(
            album_artist=album_info.artist,
            album_name=album_info.name,
            loved=_(", ❤️ loved") if album_info.loved else "",
            time=get_time_elapsed_str(last_played) if not last_played.now_playing else "",
            plays=_(" ∙ <code>{album_playcount} plays</code>").format(
                album_playcount=album_info.playcount
            )
            if album_info.playcount > 0
            else "",
        )

        if album_info.tags:
            text += f"\n\n{format_tags(album_info)}"

        image = get_biggest_lastfm_image(last_played)

        if image:
            await message.reply_photo(photo=image, caption=text)
            return

        await message.reply(text, disable_web_page_preview=True)
