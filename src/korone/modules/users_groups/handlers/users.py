# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>


from hydrogram import Client
from hydrogram.errors import PeerIdInvalid, UsernameNotOccupied
from hydrogram.types import Message

from korone.database.table import Document
from korone.decorators import router
from korone.filters import Command, CommandObject
from korone.modules.users_groups.database import get_user_by_id, get_user_by_username
from korone.utils.i18n import gettext as _


def validate_identifier(identifier: str | int) -> bool:
    if isinstance(identifier, int):
        return True
    return bool(identifier.isdigit() or identifier.startswith("@"))


async def fetch_user(message: Message, identifier: str | int) -> Document | None:
    if not validate_identifier(identifier):
        await message.reply(_("Invalid identifier provided."))
        return None

    try:
        if isinstance(identifier, int):
            user = (await get_user_by_id(identifier))[0]
        else:
            user = (await get_user_by_username(identifier.lstrip("@")))[0]
    except (PeerIdInvalid, UsernameNotOccupied, IndexError) as e:
        error_messages = {
            PeerIdInvalid: _("The provided user ID is invalid."),
            UsernameNotOccupied: _("The provided username does not exist."),
            IndexError: _("No user found with the provided identifier."),
        }
        await message.reply(error_messages[type(e)])
        return None
    return user


@router.message(Command(commands=["user", "info"]))
async def user_command(client: Client, message: Message) -> None:
    command = CommandObject(message).parse()
    user_identifier = (
        command.args or getattr(message.reply_to_message, "from_user", message.from_user).id
    )

    user = await fetch_user(message, user_identifier)
    if not user:
        return

    text = _("<b>User info</b>:\n")
    text += _("<b>ID</b>: <code>{id}</code>\n").format(id=user["id"])
    text += _("<b>First Name</b>: {first_name}\n").format(first_name=user["first_name"])
    if last_name := user.get("last_name"):
        text += _("<b>Last Name</b>: {last_name}\n").format(last_name=last_name)
    if username := user.get("username"):
        text += _("<b>Username</b>: @{username}\n").format(username=username)
    text += _("<b>User link</b>: <a href='tg://user?id={id}'>link</a>\n").format(id=user["id"])

    await message.reply(text)
