# Copyright (C) 2018 - 2020 MrYacha. All rights reserved. Source code available under the AGPL.
# Copyright (C) 2019 Aiogram
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message

from sophie_bot import bot
from sophie_bot.legacy_modules.utils.message import get_arg
from .utils.connections import chat_connection
from .utils.language import get_strings_dec
from .utils.register import register
from sophie_bot.filters.admin_rights import UserRestricting, BotHasPermissions


#
# This file is part of SophieBot.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


@register(UserRestricting(can_restrict_members=True), BotHasPermissions(can_pin_messages=True), cmds="unpin")
@chat_connection(admin=True)
@get_strings_dec('pins')
async def unpin_message(message, chat, strings):
    # support unpinning all
    if get_arg(message) in {'all'}:
        return await bot.unpin_all_chat_messages(chat['chat_id'])

    try:
        await bot.unpin_chat_message(chat['chat_id'])
    except TelegramBadRequest:
        await message.reply(strings['chat_not_modified_unpin'])
        return


@register(UserRestricting(can_restrict_members=True), BotHasPermissions(can_pin_messages=True), cmds="pin")
@get_strings_dec('pins')
async def pin_message(message: Message, strings):
    if not message.reply_to_message:
        await message.reply(strings['no_reply_msg'])
        return
    msg = message.reply_to_message.message_id
    arg = get_arg(message).lower()

    dnd = True
    loud = ['loud', 'notify']
    if arg in loud:
        dnd = False

    try:
        await bot.pin_chat_message(message.chat.id, msg, disable_notification=dnd)
    except TelegramBadRequest:
        await message.reply(strings['chat_not_modified_pin'])
