# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from datetime import UTC, datetime

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, CommandObject, IsAdmin
from korone.modules.filters.database import get_filter_info
from korone.utils.i18n import gettext as _


@router.message(Command("filterinfo") & IsAdmin)
async def filterinfo_command(client: Client, message: Message) -> None:
    command_obj = CommandObject(message).parse()

    if not command_obj.args:
        await message.reply(
            _(
                "You need to provide the name of the filter. "
                "Example: <code>/filterinfo filtername</code>"
            )
        )
        return

    filter_name = command_obj.args.lower()
    filter_info = await get_filter_info(message.chat.id, filter_name)

    if not filter_info:
        await message.reply(_("Filter '{name}' not found.").format(name=filter_name))
        return

    created_date = format_date(filter_info.created_date)
    edited_date = format_date(filter_info.edited_date)

    response_message = _(
        "<b>Filter Info</b>:\n"
        "<b>Names</b>: {names}\n"
        "<b>Content Type</b>: <code>{content_type}</code>\n"
        "<b>Created Date</b>: <i>{created_date}</i>\n"
        "<b>Creator</b>: {creator}\n"
        "<b>Edited Date</b>: <i>{edited_date}</i>\n"
        "<b>Editor</b>: {editor}"
    ).format(
        names=", ".join(filter_info.names),
        content_type=filter_info.content_type,
        created_date=created_date,
        creator=f"{filter_info.creator.first_name} {filter_info.creator.last_name}",
        edited_date=edited_date,
        editor=f"{filter_info.editor.first_name} {filter_info.editor.last_name}",
    )

    await message.reply(response_message)


def format_date(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp, tz=UTC).strftime("%d-%m-%Y %H:%M:%S %Z")
