# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, CommandObject
from korone.modules.gsm_arena.utils.keyboard import create_pagination_layout
from korone.modules.gsm_arena.utils.scraper import check_phone_details, format_phone, search_phone
from korone.utils.i18n import gettext as _


@router.message(Command(commands=["device", "specs", "d"]))
async def device_command(client: Client, message: Message) -> None:
    command = CommandObject(message).parse()

    if not command.args:
        await message.reply(
            _(
                "You should provide a device name to search. "
                "Example: <code>/device Galaxy S24</code>."
            )
        )
        return

    query = command.args
    devices = await search_phone(query)

    if not devices:
        await message.reply(_("No devices found."))
        return

    if len(devices) == 1:
        phone = await check_phone_details(devices[0].url)
        await message.reply(text=format_phone(phone))
    else:
        keyboard = create_pagination_layout(devices, query, 1)
        await message.reply(
            _("Search results for: <b>{query}</b>").format(query=query),
            reply_markup=keyboard,
        )
