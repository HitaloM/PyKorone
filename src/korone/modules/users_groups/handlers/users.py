# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.errors import PeerIdInvalid
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, CommandObject
from korone.handlers.abstract import MessageHandler
from korone.modules.users_groups.database import get_user_by_id, get_user_by_username, save_user
from korone.utils.i18n import gettext as _


class GetUserHandler(MessageHandler):
    @staticmethod
    async def fetch_user(client: Client, identifier: str | int) -> dict | None:
        try:
            if isinstance(identifier, str) and identifier.startswith("@"):
                user = (await get_user_by_username(identifier[1:]))[0]
            else:
                user_id = int(identifier) if isinstance(identifier, str) else identifier
                user = (await get_user_by_id(user_id))[0]
        except IndexError:
            try:
                users = await client.get_users(identifier)
                user = (await save_user(users[0] if isinstance(users, list) else users))[0]
            except (PeerIdInvalid, IndexError):
                return None
        return user

    @staticmethod
    @router.message(Command(commands=["user", "info"]))
    async def handle(client: Client, message: Message) -> None:
        command = CommandObject(message).parse()
        user_identifier = (
            command.args or getattr(message.reply_to_message, "from_user", message.from_user).id
        )

        user = await GetUserHandler.fetch_user(client, user_identifier)
        if not user:
            await message.reply(
                _("Invalid user ID or username.") if command.args else _("User not found.")
            )
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
