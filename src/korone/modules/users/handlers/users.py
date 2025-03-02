# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import html

from hydrogram import Client
from hydrogram.errors import PeerIdInvalid, UsernameInvalid, UsernameNotOccupied
from hydrogram.types import Message

from korone.database.table import Document
from korone.decorators import router
from korone.filters import Command, CommandObject
from korone.modules.users.database import get_user_by_id, get_user_by_username
from korone.utils.i18n import gettext as _


@router.message(Command(commands=["user", "info"]))
async def user_command(client: Client, message: Message) -> None:
    command = CommandObject(message).parse()
    identifier = (
        command.args or getattr(message.reply_to_message, "from_user", message.from_user).id
    )

    if not (isinstance(identifier, int) or identifier.isdigit() or identifier.startswith("@")):
        await message.reply(_("Invalid identifier provided."))
        return

    try:
        identifier = validate_identifier(str(identifier))
        user = await get_user(str(identifier))
        if user is None:
            raise IndexError(_("No user found with the provided identifier"))

        text = format_user_info(user)
        await message.reply(text)

    except (PeerIdInvalid, UsernameNotOccupied, IndexError, KeyError, ValueError) as e:
        await handle_error(message, e)


async def handle_error(message: Message, error: Exception) -> None:
    error_messages = {
        PeerIdInvalid: _("The provided user ID is invalid."),
        UsernameInvalid: _("The provided username is invalid."),
        UsernameNotOccupied: _("The provided username does not exist."),
        IndexError: _("No entity found with the provided identifier."),
        KeyError: _("Error accessing data."),
        ValueError: _("The provided value is not valid."),
    }
    for error_type, error_message in error_messages.items():
        if isinstance(error, error_type):
            await message.reply(error_message)
            break
    else:
        await message.reply(_("An unexpected error occurred."))


def validate_identifier(identifier: str) -> str:
    if identifier.isdigit():
        identifier_int = int(identifier)
        if not (-9223372036854775808 <= identifier_int <= 9223372036854775807):
            raise ValueError(_("Identifier out of range for SQLite INTEGER"))
        return identifier

    if identifier.startswith("@"):
        if len(identifier) < 2:
            raise ValueError(_("Username must be at least 2 characters long"))
        return identifier

    raise ValueError(_("Identifier must be a number or a username starting with @"))


async def get_user(identifier: str) -> Document:
    if identifier.isdigit():
        return (await get_user_by_id(int(identifier)))[0]
    return (await get_user_by_username(identifier.lstrip("@")))[0]


def format_user_info(user: dict) -> str:
    text = _("<b>User info</b>:\n")
    text += _("<b>ID</b>: <code>{id}</code>\n").format(id=user["id"])
    text += _("<b>First Name</b>: {first_name}\n").format(
        first_name=html.escape(user["first_name"])
    )

    if last_name := user.get("last_name"):
        text += _("<b>Last Name</b>: {last_name}\n").format(last_name=html.escape(last_name))

    if username := user.get("username"):
        text += _("<b>Username</b>: @{username}\n").format(username=username)

    text += _("<b>User link</b>: <a href='tg://user?id={id}'>link</a>\n").format(id=user["id"])
    return text
