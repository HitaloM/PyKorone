# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.handlers.message_handler import MessageHandler
from korone.modules.afk.utils import is_afk, set_afk
from korone.modules.utils.filters import Command
from korone.modules.utils.filters.command import CommandObject
from korone.utils.i18n import gettext as _


class SetAfk(MessageHandler):
    @router.message(Command("afk"))
    async def handle(self, client: Client, message: Message) -> None:
        command = CommandObject(message).parse()

        isafk = await is_afk(message.from_user.id)

        if isafk and not command.args:
            await message.reply(_("You are already AFK."))
        else:
            await set_afk(message.from_user.id, state=True, reason=command.args or None)
            if isafk:
                await message.reply(_("Your AFK status has been updated!"))
            else:
                await message.reply(_("You are now AFK."))