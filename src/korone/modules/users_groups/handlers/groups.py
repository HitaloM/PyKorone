# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M.

from hydrogram import Client
from hydrogram.enums import ChatType
from hydrogram.errors import ChannelPrivate, PeerIdInvalid, UsernameInvalid, UsernameNotOccupied
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, CommandObject
from korone.handlers.abstract import MessageHandler
from korone.modules.users_groups.database import get_chat_by_id, get_chat_by_username
from korone.utils.i18n import gettext as _


class GetGroupHandler(MessageHandler):
    @staticmethod
    async def validate_identifier(identifier: str | int) -> bool:
        if isinstance(identifier, int):
            return True
        return bool(
            identifier.isdigit()
            or (identifier.startswith("-100") and identifier[4:].isdigit())
            or identifier.startswith("@")
        )

    async def fetch_group(
        self, client: Client, message: Message, identifier: str | int
    ) -> dict | None:
        if not await self.validate_identifier(identifier):
            await message.reply(_("The provided identifier is not valid."))
            return None

        try:
            if isinstance(identifier, str) and identifier.startswith("@"):
                username = identifier[1:]
                group = (await get_chat_by_username(username))[0]
            else:
                chat_id = int(identifier)
                group = (await get_chat_by_id(chat_id))[0]
        except (
            PeerIdInvalid,
            ChannelPrivate,
            UsernameInvalid,
            UsernameNotOccupied,
            IndexError,
            KeyError,
            ValueError,
        ) as e:
            error_messages = {
                PeerIdInvalid: _("The provided group ID is invalid."),
                ChannelPrivate: _(
                    "Unable to access this channel, maybe it's private or I'm banned from it."
                ),
                UsernameInvalid: _("The provided username is invalid."),
                UsernameNotOccupied: _("The provided username does not exist."),
                IndexError: _("No group found with the provided identifier."),
                KeyError: _("Error accessing group data."),
                ValueError: _("The provided value is not valid."),
            }
            await message.reply(error_messages[type(e)])
            return None
        return group

    @router.message(Command("group"))
    async def handle(self, client: Client, message: Message) -> None:
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

        group = await self.fetch_group(client, message, group_id)
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
