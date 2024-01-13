# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client, filters
from hydrogram.enums import ChatMemberStatus, ChatType
from hydrogram.filters import Filter
from hydrogram.types import CallbackQuery, Message

from korone.config import ConfigManager


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


filters.admin = filters.create(check_admin)  # type: ignore


async def check_sudo(filter: Filter, client: Client, union: Message | CallbackQuery) -> bool:
    """
    Check if the user is a sudoer.

    This is a Hydrogram custom filter to check if the user is a sudoer. This
    filter is useful to restrict commands to sudoers only.

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
        True if the user is a sudoer, False otherwise.
    """
    is_callback = isinstance(union, CallbackQuery)
    message = union.message if is_callback else union

    if message.from_user is None:
        return False

    config = ConfigManager()
    sudoers: list[int] = config.get("korone", "SUDOERS")
    return message.from_user.id in sudoers


filters.sudo = filters.create(check_sudo)  # type: ignore
