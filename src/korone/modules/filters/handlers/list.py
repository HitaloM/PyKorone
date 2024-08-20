# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command
from korone.handlers.abstract import MessageHandler
from korone.modules.filters.database import list_filters
from korone.utils.i18n import gettext as _


class ListFilters(MessageHandler):
    @staticmethod
    @router.message(Command("filters"))
    async def handle(client: Client, message: Message) -> None:
        filters = await list_filters(message.chat.id)
        if not filters:
            await message.reply(_("No filters found for this chat."))
            return

        sorted_filters = sorted(filters, key=lambda f: f.filter_name)
        filter_list = "\n".join(
            f" - <code>{filter.filter_name}</code>" for filter in sorted_filters
        )
        await message.reply(
            _("List of filters in {chatname}:\n").format(
                chatname=message.chat.title or _("private chat")
            )
            + filter_list,
        )
