# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import re

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.handlers.abstract.message_handler import MessageHandler
from korone.modules.lastfm.database import save_lastfm_user
from korone.modules.utils.filters import Command, CommandObject
from korone.utils.i18n import gettext as _


class SetLastFMHandler(MessageHandler):
    @staticmethod
    def is_valid_username(username: str) -> bool:
        return bool(re.match("^[A-Za-z0-9]*$", username))

    @router.message(Command(commands=["setfm", "setlast"]))
    async def handle(self, client: Client, message: Message) -> None:
        command = CommandObject(message).parse()
        username = command.args

        if not username:
            await message.reply(_("You need to provide your LastFM username!"))
            return

        if not self.is_valid_username(username):
            await message.reply(
                _("LastFM username must not contain spaces or special characters!")
            )
            return

        await save_lastfm_user(user_id=message.from_user.id, username=username)
        await message.reply(_("LastFM username set successfully!"))
