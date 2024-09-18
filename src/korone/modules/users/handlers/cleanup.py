# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.errors import BadRequest
from hydrogram.types import ChatPrivileges, Message

from korone.decorators import router
from korone.filters import Command, IsGroupChat, UserIsAdmin
from korone.filters.admin import BotIsAdmin
from korone.utils.i18n import gettext as _


@router.message(Command("cleanup") & IsGroupChat & UserIsAdmin)
async def cleanup_command(client: Client, message: Message) -> None:
    if not await BotIsAdmin(
        client, message, permissions=ChatPrivileges(can_restrict_members=True), show_alert=True
    ):
        return

    sent = await message.reply(_("Removing deleted accounts..."))

    try:
        members = client.get_chat_members(message.chat.id)
        members = [member async for member in members] if members else []  # type: ignore
    except Exception:
        await sent.edit(_("Failed to fetch members."))
        return

    if not members:
        await sent.edit(_("No members found."))
        return

    deleted = 0
    for member in members:
        if member.user.is_deleted:
            try:
                await client.ban_chat_member(message.chat.id, member.user.id)
                await client.unban_chat_member(message.chat.id, member.user.id)
                deleted += 1
            except BadRequest:
                continue

    if deleted > 0:
        await sent.edit(_("Removed {count} deleted accounts.").format(count=deleted))
        return

    await sent.edit(_("No deleted accounts found."))
