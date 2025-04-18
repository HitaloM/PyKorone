# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, CommandObject, UserIsAdmin
from korone.modules.filters.database import delete_filter, list_filters, update_filters_cache
from korone.utils.i18n import gettext as _


@router.message(Command("delfilter") & UserIsAdmin)
async def delfilter_command(client: Client, message: Message) -> None:
    command_obj = CommandObject(message).parse()

    if not command_obj.args:
        await message.reply(
            _(
                "You need to provide the name of the filter to delete. "
                "Example: <code>/delfilter filtername</code>"
            )
        )
        return

    filter_name = command_obj.args.lower()
    existing_filters = await list_filters(message.chat.id)

    if any(filter_name in filter.names for filter in existing_filters):
        await delete_filter(message.chat.id, (filter_name,))
        await update_filters_cache(message.chat.id)
        await message.reply(
            _("Filter '<code>{filter_name}</code>' has been deleted.").format(
                filter_name=filter_name
            )
        )
        return

    await message.reply(
        _("Filter '<code>{filter_name}</code>' does not exist.").format(filter_name=filter_name)
    )
