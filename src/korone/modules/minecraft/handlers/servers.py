# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import re

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, CommandObject
from korone.modules.minecraft.utils.servers import MinecraftServerStatus
from korone.utils.i18n import gettext as _

ADDRESS_REGEX = re.compile(
    r"^((?:(?:[0-9]{1,3}\.){3}[0-9]{1,3})(?::[0-9]{1,5})?|"
    r"(?:(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,})(?::[0-9]{1,5})?)$"
)


@router.message(Command(commands=["mcserver", "mcstatus"]))
async def handle_mcserver_command(client: Client, message: Message) -> None:
    command = CommandObject(message).parse()

    if not command.args:
        await message.reply(
            _(
                "You need to provide a server address. "
                "Example: <code>/mcserver mc.hypixel.net</code>."
            )
        )
        return

    address = command.args

    if not ADDRESS_REGEX.match(address):
        await message.reply(
            _(
                "Invalid server address. Please provide a valid "
                "IP address or hostname, optionally with a port."
            )
        )
        return

    server_status = await MinecraftServerStatus.from_address(address)
    if not server_status.online:
        await message.reply(_("This Minecraft server is offline."))
        return

    status_message = _(
        "<b>Server Status for {address}</b>:\n"
        "<b>Players</b>: {player_count}\n"
        "<b>Version:</b> {version}\n"
        "<b>MOTD</b>: <pre>{motd}</pre>\n"
    ).format(
        address=address,
        player_count=server_status.player_count,
        version=server_status.version,
        motd=" ".join(server_status.motd),
    )

    await message.reply(status_message, disable_web_page_preview=True)
