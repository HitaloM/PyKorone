# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.handlers.abstract.message_handler import MessageHandler
from korone.modules.lastfm.database import save_lastfm_user
from korone.modules.utils.filters import Command, CommandObject
from korone.utils.i18n import gettext as _


class SetLastFMHandler(MessageHandler):
    @staticmethod
    @router.message(Command(commands=["setfm", "setlast"]))
    async def handle(client: Client, message: Message) -> None:
        command = CommandObject(message).parse()
        args = command.args

        if not args:
            await message.reply(_("You need to provide your LastFM username!"))
            return

        if not isinstance(args, str) or " " in args:
            await message.reply(_("LastFM username must not contain spaces!"))
            return

        await save_lastfm_user(user_id=message.from_user.id, username=args)
        await message.reply(_("LastFM username set successfully!"))
