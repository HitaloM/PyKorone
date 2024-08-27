# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.errors import BadRequest
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, IsAdmin, IsGroupChat
from korone.utils.i18n import gettext as _


async def fetch_members(client: Client, chat_id: int) -> list:
    members = client.get_chat_members(chat_id)
    if not members:
        return []
    return [member async for member in members]  # type: ignore


async def remove_deleted_accounts(client: Client, chat_id: int, members: list) -> int:
    deleted = 0
    for member in members:
        if member.user.is_deleted:
            try:
                await client.ban_chat_member(chat_id, member.user.id)
                await client.unban_chat_member(chat_id, member.user.id)
                deleted += 1
            except BadRequest:
                continue
    return deleted


@router.message(Command("cleanup") & IsGroupChat & IsAdmin)
async def cleanup_command(client: Client, message: Message) -> None:
    sent = await message.reply(_("Removing deleted accounts..."))

    members = await fetch_members(client, message.chat.id)
    if not members:
        await sent.edit(_("No members found."))
        return

    deleted = await remove_deleted_accounts(client, message.chat.id, members)
    if deleted > 0:
        await sent.edit(_("Removed {count} deleted accounts.").format(count=deleted))
    else:
        await sent.edit(_("No deleted accounts found."))
