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
    @router.message(Command("afk"))
    async def handle(self, client: Client, message: Message) -> None:
        command = CommandObject(message).parse()
        user_id = message.from_user.id
        isafk = await is_afk(user_id)

        if await self.is_already_afk(isafk, command.args, message):
            return

        if await self.is_invalid_afk_message(command.args, message):
            return

        await set_afk(user_id, state=True, reason=command.args or None)
        await self.send_afk_response(isafk, message)

    @staticmethod
    async def is_already_afk(isafk: bool, args: str | None, message: Message) -> bool:
        if isafk and not args:
            await message.reply(_("You are already AFK."))
            return True
        return False

    @staticmethod
    async def is_invalid_afk_message(args: str | None, message: Message) -> bool:
        if args and len(args) > 64:
            await message.reply(_("The maximum length of the AFK message is 64 characters."))
            return True
        return False

    @staticmethod
    async def send_afk_response(isafk: bool, message: Message) -> None:
        if isafk:
            await message.reply(_("Your AFK status has been updated!"))
        else:
            await message.reply(_("You are now AFK."))
