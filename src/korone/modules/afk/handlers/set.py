# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, CommandObject
from korone.modules.afk.database import is_afk, set_afk
from korone.utils.i18n import gettext as _


@router.message(Command("afk"))
async def afk_command(client: Client, message: Message) -> None:
    command = CommandObject(message).parse()
    user_id = message.from_user.id
    isafk = await is_afk(user_id)

    if isafk and not command.args:
        await message.reply(_("You are already AFK."))
        return

    if command.args and len(command.args) > 64:
        await message.reply(_("The maximum length of the AFK message is 64 characters."))
        return

    await set_afk(user_id, state=True, reason=command.args or None)

    if isafk:
        await message.reply(_("Your AFK status has been updated!"))
    else:
        await message.reply(_("You are now AFK."))
