# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.errors import BadRequest
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, IsAdmin, IsGroupChat
from korone.utils.i18n import gettext as _


@router.message(Command("cleanup") & IsGroupChat & IsAdmin)
async def cleanup_command(client: Client, message: Message) -> None:
    deleted = 0
    sent = await message.reply(_("Removing deleted accounts..."))

    members = client.get_chat_members(message.chat.id)
    if not members:
        await sent.edit(_("No members found."))
        return

    async for member in members:  # type: ignore
        if member.user.is_deleted:
            try:
                await client.ban_chat_member(message.chat.id, member.user.id)
                await client.unban_chat_member(message.chat.id, member.user.id)
                deleted += 1
            except BadRequest:
                continue

    if deleted > 0:
        await sent.edit(_("Removed {count} deleted accounts.").format(count=deleted))
    else:
        await sent.edit(_("No deleted accounts found."))
