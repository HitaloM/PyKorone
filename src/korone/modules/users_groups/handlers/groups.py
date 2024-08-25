# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M.


from hydrogram import Client
from hydrogram.enums import ChatType
from hydrogram.errors import UsernameInvalid, UsernameNotOccupied
from hydrogram.types import Message

from korone.database.table import Document
from korone.decorators import router
from korone.filters import Command, CommandObject
from korone.modules.users_groups.database import get_chat_by_id
from korone.utils.i18n import gettext as _


def validate_identifier(identifier: str | int) -> bool:
    if isinstance(identifier, int):
        return True
    return bool(
        identifier.isdigit()
        or (identifier.startswith("-100") and identifier[4:].isdigit())
        or identifier.startswith("@")
    )


async def fetch_group(message: Message, identifier: str | int) -> Document | None:
    if not validate_identifier(identifier):
        await message.reply(_("The provided identifier is not valid."))
        return None

    try:
        if isinstance(identifier, int) or identifier.isdigit():
            return (await get_chat_by_id(int(identifier)))[0]
        chat_id = int(identifier)
        return (await get_chat_by_id(chat_id))[0]
    except (UsernameInvalid, UsernameNotOccupied, IndexError, KeyError, ValueError) as e:
        error_messages = {
            UsernameInvalid: _("The provided username is invalid."),
            UsernameNotOccupied: _("The provided username does not exist."),
            IndexError: _("No group found with the provided identifier."),
            KeyError: _("Error accessing group data."),
            ValueError: _("The provided value is not valid."),
        }
        await message.reply(error_messages[type(e)])
        return None


@router.message(Command("group"))
async def group_command(client: Client, message: Message) -> None:
    command = CommandObject(message).parse()
    group_id = command.args or message.chat.id

    if message.chat.type == ChatType.PRIVATE and not command.args:
        await message.reply(
            _(
                "You should provide a group ID or username. "
                "Example: <code>/group @username</code>."
            )
        )
        return

    group = await fetch_group(message, group_id)
    if not group:
        return

    text = _("<b>Group info</b>:\n")
    text += _("<b>ID</b>: <code>{id}</code>\n").format(id=group["id"])
    text += _("<b>Title</b>: {title}\n").format(title=group["title"])
    if username := group.get("username"):
        text += _("<b>Username</b>: @{username}\n").format(username=username)
    if group_type := group["type"]:
        text += _("<b>Type</b>: {type}\n").format(type=group_type)

    await message.reply(text)
