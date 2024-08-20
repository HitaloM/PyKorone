# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import re

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, CommandObject
from korone.handlers.abstract import MessageHandler
from korone.modules.filters.database import FilterStatus, save_filter
from korone.modules.filters.utils.content_type import SUPPORTED_CONTENTS
from korone.utils.i18n import gettext as _


class SaveFilter(MessageHandler):
    @router.message(Command("filter"))
    async def handle(self, client: Client, message: Message) -> None:
        command_obj = CommandObject(message).parse()
        if not command_obj.args or (not command_obj.args and not message.reply_to_message):
            await message.reply(
                _(
                    "You need to provide a name for the filter. "
                    "Example: <code>/filter filtername</code>"
                )
            )
            return

        filters = self.parse_args(command_obj.args.lower(), message.reply_to_message)
        if not filters:
            await message.reply(_("Invalid filter format."))
            return

        await self.process_filters(message, filters)

    async def process_filters(self, message: Message, filters: dict[str, str]) -> None:
        content_type, filter_message, file_id = self.get_message_details(message.reply_to_message)
        results = []

        for filter_name, filter_msg in filters.items():
            result = await save_filter(
                message.chat.id,
                filter_name,
                filter_msg or filter_message,
                content_type,
                message.from_user.id,
                message.from_user.id,
                file_id,
            )
            results.append((filter_name, result))

        await self.reply_filter_status(message, results)

    @staticmethod
    async def reply_filter_status(
        message: Message, results: list[tuple[str, FilterStatus]]
    ) -> None:
        saved_filters = [
            f"<code>{name}</code>" for name, status in results if status == FilterStatus.SAVED
        ]
        updated_filters = [
            f"<code>{name}</code>" for name, status in results if status == FilterStatus.UPDATED
        ]

        if saved_filters or updated_filters:
            combined_message = _("Filters in {chatname}:\n").format(
                chatname=message.chat.title or _("private chat")
            )

            if saved_filters:
                combined_message += _("{count} saved:\n{filters}\n").format(
                    count=len(saved_filters),
                    filters="\n".join(f" - {filter}" for filter in saved_filters),
                )

            if updated_filters:
                combined_message += _("{count} updated:\n{filters}").format(
                    count=len(updated_filters),
                    filters="\n".join(f" - {filter}" for filter in updated_filters),
                )

            await message.reply(combined_message)

    def parse_args(self, args: str, reply_message: Message | None = None) -> dict[str, str] | None:
        if match := re.match(r"^\((.*?)\)\s*(.*)$", args):
            return self._parse_multiple_filters(match, reply_message)

        if reply_message and not args.strip():
            return {args.strip().strip('"'): ""}

        return self._parse_single_filter(args, reply_message)

    @staticmethod
    def _parse_multiple_filters(
        match: re.Match, reply_message: Message | None = None
    ) -> dict[str, str]:
        filter_names, message = match.groups()
        message = message if not reply_message or message.strip() else ""
        return {
            filter_name.strip().strip('"'): message
            for filter_name in re.split(r',\s*(?=(?:[^"]*"[^"]*")*[^"]*$)', filter_names)
        }

    @staticmethod
    def _parse_single_filter(args: str, reply_message: Message | None = None) -> dict[str, str]:
        if reply_message:
            return {args.strip().strip('"'): ""}

        if match := re.match(r'^"([^"]+)"\s+(.*)$|^(\S+)\s+(.*)$', args):
            filter_name, message = (
                match.group(1) or match.group(3),
                match.group(2) or match.group(4),
            )
            return {filter_name.strip().strip('"'): message}
        return {}

    @staticmethod
    def get_message_details(message: Message | None) -> tuple[str, str, str | None]:
        if not message:
            return "text", "", None

        content_type = next(
            (
                content_type
                for media_type, content_type in SUPPORTED_CONTENTS.items()
                if getattr(message, str(media_type.value), None)
            ),
            "text",
        )
        filter_message, file_id = (
            (message.text or message.caption or "", None)
            if content_type == "text"
            else next(
                (
                    (message.caption or "", media.file_id)
                    for media_type in SUPPORTED_CONTENTS
                    if (media := getattr(message, str(media_type.value), None))
                ),
                ("", None),
            )
        )
        return content_type, filter_message, file_id
