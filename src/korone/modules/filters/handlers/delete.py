# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, CommandObject, IsAdmin
from korone.handlers.abstract import MessageHandler
from korone.modules.filters.database import delete_filter, list_filters, update_filters_cache
from korone.utils.i18n import gettext as _


class DeleteFilter(MessageHandler):
    @router.message(Command("delfilter") & IsAdmin)
    async def handle(self, client: Client, message: Message) -> None:
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

        if not self._filter_exists(filter_name, existing_filters):
            await message.reply(
                _("Filter '<code>{filter_name}</code>' does not exist.").format(
                    filter_name=filter_name
                )
            )
            return

        await delete_filter(message.chat.id, (filter_name,))
        await update_filters_cache(message.chat.id)
        await message.reply(
            _("Filter '<code>{filter_name}</code>' has been deleted.").format(
                filter_name=filter_name
            )
        )

    @staticmethod
    def _filter_exists(filter_name: str, existing_filters: list) -> bool:
        return any(filter_name in filter.names for filter in existing_filters)
