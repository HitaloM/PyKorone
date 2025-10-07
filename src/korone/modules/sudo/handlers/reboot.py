# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, IsSudo
from korone.modules.sudo.utils import restart_bot


@router.message(Command("reboot", disableable=False) & IsSudo)
async def reboot_command(client: Client, message: Message) -> None:
    sent = await message.reply("Starting reboot...")
    await restart_bot(sent, "Rebooting...")
