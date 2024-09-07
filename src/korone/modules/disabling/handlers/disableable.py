# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, IsAdmin
from korone.modules.core import COMMANDS
from korone.utils.i18n import gettext as _


@router.message(Command("disableable", disableable=False) & IsAdmin)
async def disableable_command(client: Client, message: Message) -> None:
    disableable_commands = sorted([cmd for cmd in COMMANDS if "parent" not in COMMANDS[cmd]])

    if not disableable_commands:
        await message.reply(_("No commands can be disabled."))
        return

    text = _("The following commands can be disabled:\n")
    text += "".join(f"- <code>{cmd}</code>\n" for cmd in disableable_commands)

    await message.reply(text)
