# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>


from datetime import UTC, datetime

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command
from korone.handlers.abstract.message_handler import MessageHandler
from korone.modules.lastfm.database import get_lastfm_user
from korone.modules.lastfm.utils import LastFMClient, LastFMError, get_biggest_lastfm_image
from korone.utils.i18n import gettext as _


class LastFMUserHandler(MessageHandler):
    @staticmethod
    @router.message(Command(commands=["lfmu", "flex"]))
    async def handle(client: Client, message: Message) -> None:
        last_fm_user = await get_lastfm_user(message.from_user.id)
        if not last_fm_user:
            await message.reply(_("You need to set your LastFM username first!"))
            return

        last_fm = LastFMClient()

        try:
            user_info = await last_fm.get_user_info(last_fm_user)
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

        registered = datetime.fromtimestamp(user_info.registered, tz=UTC).strftime("%d-%m-%Y")

        user_mention = message.from_user.mention()

        image = get_biggest_lastfm_image(user_info)

        text = _(
            "User: <b>{user}</b>\n\n"
            "Total scrobbles: <code>{playcount}</code>\n"
            "Tracks scrobbled: <code>{track_count}</code>\n"
            "Artists scrobbled: <code>{artist_count}</code>\n"
            "Albums scrobbled: <code>{album_count}</code>\n"
            "\nRegistered: <i>{registered}</i>"
        ).format(
            user=user_mention,
            playcount=f"{user_info.playcount:,}",
            track_count=f"{user_info.track_count:,}",
            artist_count=f"{user_info.artist_count:,}",
            album_count=f"{user_info.album_count:,}",
            registered=registered,
        )

        if image:
            await message.reply_photo(photo=image, caption=text)
            return

        await message.reply(text, disable_web_page_preview=True)
