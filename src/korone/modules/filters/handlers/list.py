# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command
from korone.modules.filters.database import get_filters_cache, list_filters
from korone.utils.i18n import gettext as _


@router.message(Command("filters"))
async def filters_command(client: Client, message: Message) -> None:
    filters = await get_filters_cache(message.chat.id) or await list_filters(message.chat.id)
    if not filters:
        await message.reply(_("No filters found for this chat."))
        return

    filter_names = sorted(filter_name for filter in filters for filter_name in filter.names)
    filter_list = "\n".join(f" - <code>{filter_name}</code>" for filter_name in filter_names)

    response_message = _("List of filters in {chatname}:\n{filter_list}").format(
        chatname=message.chat.title or _("private chat"), filter_list=filter_list
    )

    await message.reply(response_message)
