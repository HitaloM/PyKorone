# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

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
                    "Invalid filter format. Make sure to use the correct syntax."
                    "Check <code>/help</code> for more information."
                )
            )
            return

        await self._process_and_save_filters(message, filters)

    async def _process_and_save_filters(self, message: Message, filters: dict[str, str]) -> None:
        results = []

        for filter_name, filter_content in filters.items():
            save_data = await parse_saveable(
                message, filter_content or "", allow_reply_message=True
            )
            if not save_data:
                await message.reply(_("Something went wrong while saving the filter."))
                return

            result = await save_filter(
                chat_id=message.chat.id,
                filter_text=filter_name,
                message_content=save_data.text,
                content_type=save_data.file.file_type if save_data.file else "text",
                creator_id=message.from_user.id,
                editor_id=message.from_user.id,
                file_id=save_data.file.file_id if save_data.file else "",
            )
            results.append((filter_name, result))

        await self._reply_filter_status(message, results)

    @staticmethod
    async def _reply_filter_status(
        message: Message, results: list[tuple[str, FilterStatus]]
    ) -> None:
        saved_filters = [
            f"<code>{name}</code>" for name, status in results if status == FilterStatus.SAVED
        ]
        updated_filters = [
            f"<code>{name}</code>" for name, status in results if status == FilterStatus.UPDATED
        ]

        if not saved_filters and not updated_filters:
            return

        response_message = _("Filters in {chatname}:\n").format(
            chatname=message.chat.title or _("private chat")
        )

        if saved_filters:
            response_message += _("{count} saved:\n{filters}\n").format(
                count=len(saved_filters),
                filters="\n".join(f" - {filter}" for filter in saved_filters),
            )

        if updated_filters:
            response_message += _("{count} updated:\n{filters}").format(
                count=len(updated_filters),
                filters="\n".join(f" - {filter}" for filter in updated_filters),
            )

        await message.reply(response_message)
