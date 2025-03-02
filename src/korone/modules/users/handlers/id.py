# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command
from korone.utils.i18n import gettext as _


@router.message(Command("id"))
async def id_command(client: Client, message: Message) -> None:
    user_id = message.from_user.id
    text = _("Your ID is <code>{id}</code>").format(id=user_id)

    if message.chat.id == user_id and not message.reply_to_message:
        await message.reply(text)
        return

    if message.chat.id != user_id:
        text += _("\nChat ID: <code>{id}</code>").format(id=message.chat.id)

    if message.reply_to_message:
        reply_user_id = message.reply_to_message.from_user.id
        if reply_user_id != user_id:
            text += _("\n{user} ID: <code>{id}</code>").format(
                user=message.reply_to_message.from_user.mention,
                id=reply_user_id,
            )

        if message.reply_to_message.forward_from:
            forwarded_user_id = message.reply_to_message.forward_from.id
            if forwarded_user_id not in {user_id, reply_user_id}:
                text += _("\nForwarded user ID: <code>{id}</code>").format(id=forwarded_user_id)

    await message.reply(text)
