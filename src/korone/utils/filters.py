# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client, filters
from hydrogram.enums import ChatMemberStatus, ChatType
from hydrogram.filters import Filter
from hydrogram.types import CallbackQuery, Message

from korone.modules.core import COMMANDS
from korone.utils.commands import get_command_name
from korone.utils.logging import log


async def check_admin(filter: Filter, client: Client, union: Message | CallbackQuery) -> bool:
    """
    Check if the user is an administrator in the chat.

    This is a Hydrogram custom filter to check if the user is an administrator
    in the chat. This filter is useful to restrict commands to administrators
    only.

    Parameters
    ----------
    filter : hydrogram.filters.Filter
        The filter object.
    client : hydrogram.Client
        The client object used to interact with the Telegram API.
    union : hydrogram.types.CallbackQuery or hydrogram.types.Message
        The message or callback query object.

    Returns
    -------
    bool
        True if the user is an administrator, False otherwise.
    """
    is_callback = isinstance(union, CallbackQuery)
    message = union.message if is_callback else union

    if message.from_user is None:
        return False

    if message.chat.type == ChatType.PRIVATE:
        return True

    user = await client.get_chat_member(message.chat.id, message.from_user.id)
    return user.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)


is_admin = filters.create(check_admin)


async def togglable(filter: Filter, client: Client, update: Message) -> bool:
    """
    Filter to handle state of command for Pyrogram's Handlers.

    This is a Hydrogram custom filter to handle the state of a command.

    Parameters
    ----------
    filter : hydrogram.filters.Filter
        The filter object.
    client : hydrogram.Client
        The client object used to interact with the Telegram API.
    update : hydrogram.types.Message
        The message object.

    Returns
    -------
    bool
        True if it handles the command, False otherwise.
    """

    if update.chat is None or update.chat.id is None:
        return False

    command: str = get_command_name(update)

    log.debug("command: %s", command)

    if command not in COMMANDS:
        return False

    if "parent" in COMMANDS[command]:
        command = COMMANDS[command]["parent"]

    if update.chat.id not in COMMANDS[command]["chat"]:
        return True

    return COMMANDS[command]["chat"][update.chat.id]


is_togglable = filters.create(togglable)
