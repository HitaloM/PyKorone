# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M.

from hydrogram import Client
from hydrogram.enums import ChatType
from hydrogram.errors import UsernameInvalid, UsernameNotOccupied
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, CommandObject
from korone.modules.users_groups.database import get_chat_by_id, get_chat_by_username
from korone.utils.i18n import gettext as _


@router.message(Command("group"))
async def group_command(client: Client, message: Message) -> None:
    command = CommandObject(message).parse()
    identifier = command.args or message.chat.id

    if message.chat.type == ChatType.PRIVATE and not command.args:
        await message.reply(
            _(
                "You should provide a group ID or username. "
                "Example: <code>/group @username</code>."
            )
        )
        return

    try:
        if not str(identifier).isdigit():
            msg = "Identifier must be a number"
            raise ValueError(msg)

        identifier = int(identifier)
        if not (-9223372036854775808 <= identifier <= 9223372036854775807):
            msg = "Identifier out of range for SQLite INTEGER"
            raise ValueError(msg)

        if isinstance(identifier, int) or identifier.isdigit():
            group = (await get_chat_by_id(identifier))[0]
        else:
            group = (await get_chat_by_username(identifier))[0]

        if group is None:
            msg = "No group found with the provided identifier"
            raise IndexError(msg)

        text = _("<b>Group info</b>:\n")
        text += _("<b>ID</b>: <code>{id}</code>\n").format(id=group["id"])
        text += _("<b>Title</b>: {title}\n").format(title=group["title"])
        if username := group.get("username"):
            text += _("<b>Username</b>: @{username}\n").format(username=username)
        if group_type := group["type"]:
            text += _("<b>Type</b>: {type}\n").format(type=group_type)

        await message.reply(text)

    except (UsernameInvalid, UsernameNotOccupied, IndexError, KeyError, ValueError) as e:
        error_messages = {
            UsernameInvalid: _("The provided username is invalid."),
            UsernameNotOccupied: _("The provided username does not exist."),
            IndexError: _("No group found with the provided identifier."),
            KeyError: _("Error accessing group data."),
            ValueError: _("The provided value is not valid."),
        }
        await message.reply(error_messages[type(e)])
