# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, CommandObject
from korone.handlers.abstract import MessageHandler
from korone.modules.afk.database import is_afk, set_afk
from korone.utils.i18n import gettext as _


class SetAfk(MessageHandler):
    @staticmethod
    @router.message(Command("afk"))
    async def handle(client: Client, message: Message) -> None:
        command = CommandObject(message).parse()
        isafk = await is_afk(message.from_user.id)

        if isafk and not command.args:
            await message.reply(_("You are already AFK."))
            return

        if command.args and len(command.args) > 64:
            await message.reply(_("The maximum length of the AFK message is 64 characters."))
            return

        await set_afk(message.from_user.id, state=True, reason=command.args or None)

        if isafk:
            await message.reply(_("Your AFK status has been updated!"))
            return

        await message.reply(_("You are now AFK."))
