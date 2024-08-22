# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, CommandObject
from korone.handlers.abstract import MessageHandler
from korone.modules.filters.database import FilterStatus, save_filter
from korone.modules.filters.utils import parse_args, parse_saveable
from korone.utils.i18n import gettext as _


class SaveFilter(MessageHandler):
    @router.message(Command("filter"))
    async def handle(self, client: Client, message: Message) -> None:
        command_obj = CommandObject(message).parse()

        if not command_obj.args:
            await message.reply(
                _(
                    "You need to provide a name for the filter. "
                    "Example: <code>/filter filtername</code>"
                )
            )
            return

        filters = parse_args(command_obj.args.lower(), message.reply_to_message)
        if not filters:
            await message.reply(
                _(
                    "Invalid filter format. Make sure to use the correct syntax. "
                    "Check <code>/help</code> for more information."
                )
            )
            return

        await self._process_and_save_filters(message, filters)

    async def _process_and_save_filters(
        self, message: Message, filters: tuple[tuple[str, ...], str]
    ) -> None:
        filter_names, filter_content = filters
        tasks = [self._save_single_filter(message, filter_names, filter_content)]
        results = await asyncio.gather(*tasks)
        await self._reply_filter_status(message, results)

    @staticmethod
    async def _save_single_filter(
        message: Message, filter_names: tuple[str, ...], filter_content: str
    ) -> tuple[str, FilterStatus]:
        save_data = await parse_saveable(message, filter_content or "", allow_reply_message=True)
        if not save_data:
            await message.reply(_("Something went wrong while saving the filter."))
            return ", ".join(filter_names), FilterStatus.FAILED

        result = await save_filter(
            chat_id=message.chat.id,
            filter_names=filter_names,
            message_content=save_data.text,
            content_type=save_data.file.file_type if save_data.file else "text",
            creator_id=message.from_user.id,
            editor_id=message.from_user.id,
            file_id=save_data.file.file_id if save_data.file else "",
        )
        return ", ".join(filter_names), result

    @staticmethod
    async def _reply_filter_status(
        message: Message, results: list[tuple[str, FilterStatus]]
    ) -> None:
        saved_filters = [
            name.split(", ") for name, status in results if status == FilterStatus.SAVED
        ]
        updated_filters = [
            name.split(", ") for name, status in results if status == FilterStatus.UPDATED
        ]

        if not saved_filters and not updated_filters:
            return

        response_message = [
            _("Filters in {chatname}:\n").format(chatname=message.chat.title or _("private chat"))
        ]

        if saved_filters:
            response_message.append(
                _("{count} saved:\n{filters}\n").format(
                    count=sum(len(names) for names in saved_filters),
                    filters="\n".join(
                        f" - <code>{filter_name}</code>"
                        for names in saved_filters
                        for filter_name in names
                    ),
                )
            )

        if updated_filters:
            response_message.append(
                _("{count} updated:\n{filters}").format(
                    count=sum(len(names) for names in updated_filters),
                    filters="\n".join(
                        f" - <code>{filter_name}</code>"
                        for names in updated_filters
                        for filter_name in names
                    ),
                )
            )

        await message.reply("".join(response_message))
