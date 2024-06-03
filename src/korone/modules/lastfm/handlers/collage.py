# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from pathlib import Path

from hairydogm.chat_action import ChatActionSender
from hydrogram import Client
from hydrogram.enums import ChatAction
from hydrogram.types import Message

from korone.decorators import router
from korone.handlers.abstract.message_handler import MessageHandler
from korone.modules.lastfm.database import get_lastfm_user
from korone.modules.lastfm.utils import (
    LastFMClient,
    LastFMError,
    create_album_collage,
    parse_collage_arg,
)
from korone.modules.lastfm.utils.api import TimePeriod
from korone.modules.utils.filters import Command, CommandObject
from korone.utils.i18n import gettext as _


class CollageHandler(MessageHandler):
    @staticmethod
    @router.message(Command("collage"))
    async def handle(client: Client, message: Message) -> None:
        last_fm_user = await get_lastfm_user(message.from_user.id)
        if not last_fm_user:
            await message.reply(_("You need to set your LastFM username first!"))
            return

        command = CommandObject(message).parse()
        args = command.args

        collage_size = 3
        period = TimePeriod.AllTime
        show_text = True

        if args:
            collage_size, period, __, no_text = parse_collage_arg(args)
            show_text = not no_text

        last_fm = LastFMClient()

        async with ChatActionSender(
            client=client, chat_id=message.chat.id, action=ChatAction.UPLOAD_PHOTO
        ):
            try:
                top_items = await last_fm.get_top_albums(
                    last_fm_user, period=period.value, limit=collage_size**2
                )
            except LastFMError as e:
                error_message = str(e)
                if error_message == "User not found":
                    await message.reply(
                        _("Your LastFM username was not found! Try setting it again.")
                    )
                else:
                    await message.reply(
                        _(
                            "An error occurred while fetching your LastFM data!\n"
                            "Error:<i>{error}</i>"
                        ).format(error=error_message)
                    )
                return

            collage_path = await create_album_collage(
                top_items, collage_size=(collage_size, collage_size), show_text=show_text
            )

            caption = (
                f"{message.from_user.mention()}'s {period.value} {collage_size}x{collage_size} "
                "album collage"
            )

            await message.reply_photo(photo=collage_path, caption=caption)

        Path(collage_path).unlink(missing_ok=True)
