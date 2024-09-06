# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M.

from hydrogram import Client
from hydrogram.enums import ChatType
from hydrogram.errors import UsernameInvalid, UsernameNotOccupied
from hydrogram.types import Message

from korone.database.table import Document
from korone.decorators import router
from korone.filters import Command, CommandObject
from korone.modules.users_groups.database import get_chat_by_id, get_chat_by_username
from korone.modules.users_groups.utils import handle_error
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
        identifier = validate_identifier(str(identifier))
        group = await get_group(str(identifier))
        if group is None:
            raise IndexError(_("No group found with the provided identifier"))

        text = format_group_info(group)
        await message.reply(text)

    except (UsernameInvalid, UsernameNotOccupied, IndexError, KeyError, ValueError) as e:
        await handle_error(message, e)


def validate_identifier(identifier: str) -> int:
    if identifier.isdigit() or (identifier.startswith("-100") and identifier[4:].isdigit()):
        identifier_int = int(identifier)
    else:
        raise ValueError(_("Identifier must be a number or start with -100 followed by digits"))

    if not (-9223372036854775808 <= identifier_int <= 9223372036854775807):
        raise ValueError(_("Identifier out of range for SQLite INTEGER"))

    return identifier_int


async def get_group(identifier: str) -> Document:
    if identifier.isdigit() or (identifier.startswith("-100") and identifier[4:].isdigit()):
        return (await get_chat_by_id(int(identifier)))[0]
    return (await get_chat_by_username(identifier))[0]


def format_group_info(group: dict) -> str:
    text = _("<b>Group info</b>:\n")
    text += _("<b>ID</b>: <code>{id}</code>\n").format(id=group["id"])
    text += _("<b>Title</b>: {title}\n").format(title=group["title"])

    if username := group.get("username"):
        text += _("<b>Username</b>: @{username}\n").format(username=username)

    if group_type := group["type"]:
        text += _("<b>Type</b>: {type}\n").format(type=group_type)

    return text
