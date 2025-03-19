# Copyright (C) 2018 - 2020 MrYacha. All rights reserved. Source code available under the AGPL.
# Copyright (C) 2019 Aiogram

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

from aiogram import F, Router, flags
from aiogram.exceptions import TelegramForbiddenError
from aiogram.filters import CommandStart
from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from ass_tg.types import BooleanArg, IntArg

from sophie_bot.modules.legacy_modules.utils.connections import (
    chat_connection,
    get_connection_data,
    set_connected_chat,
)
from sophie_bot.modules.legacy_modules.utils.deep_linking import get_start_link
from sophie_bot.modules.legacy_modules.utils.language import get_strings_dec
from sophie_bot.modules.legacy_modules.utils.message import get_arg, get_args_str
from sophie_bot.modules.legacy_modules.utils.register import register
from sophie_bot.modules.legacy_modules.utils.user_details import (
    get_chat_dec,
    is_user_admin,
)
from sophie_bot.modules.notes.utils.buttons_processor.legacy import BUTTONS
from sophie_bot.services.bot import bot, dp
from sophie_bot.services.db import db
from sophie_bot.services.redis import redis
from sophie_bot.utils.i18n import lazy_gettext as l_

__module_name__ = l_("Connections")
__module_emoji__ = "🔐"

router = Router(name="connection")


class ConnectToChatCb(CallbackData, prefix="connect_to_chat_cb"):
    chat_id: int


@get_strings_dec("connections")
async def def_connect_chat(message: Message, user_id, chat_id, chat_title, strings, edit=False):
    await set_connected_chat(user_id, chat_id)

    text = strings["pm_connected"].format(chat_name=chat_title)
    if edit:
        await message.edit_text(text)
    else:
        await message.reply(text)


# In chat - connect directly to chat
@register(router, cmds="connect", only_groups=True, no_args=True)
@flags.help(description=l_("Connects PM with bot to the current chat."))
@get_strings_dec("connections")
async def connect_to_chat_direct(message: Message, strings):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id == 1087968824:
        # just warn the user that connections with admin rights doesn't work
        return await message.reply(
            strings["anon_admin_conn"],
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text=strings["click_here"], callback_data="anon_conn_cb")]]
            ),
        )

    chat = await db.chat_list.find_one({"chat_id": chat_id})
    chat_title = chat["chat_title"] if chat is not None else message.chat.title
    text = strings["pm_connected"].format(chat_name=chat_title)

    try:
        await bot.send_message(user_id, text)
        await def_connect_chat(message, user_id, chat_id, chat_title)
    except TelegramForbiddenError:
        await message.reply(strings["connected_pm_to_me"].format(chat_name=chat_title))
        redis.set(f"sophie_connected_start_state:{str(user_id)}", 1)


# In pm without args - show last connected chats
@register(router, cmds="connect", no_args=True, only_pm=True)
@flags.help(description=l_("Connects to the latest chat."))
@get_strings_dec("connections")
@chat_connection()
async def connect_chat_keyboard(message: Message, strings, chat):
    connected_data = await get_connection_data(message.from_user.id)
    if not connected_data:
        return await message.reply(strings["u_wasnt_connected"])

    if chat["status"] != "private":
        text = strings["connected_chat"].format(chat_name=chat["chat_title"])
    elif "command" in connected_data:
        if chat := await db.chat_list.find_one({"chat_id": connected_data["chat_id"]}):
            chat_title = chat["chat_title"]
        else:
            chat_title = connected_data["chat_id"]
        text = strings["connected_chat:cmds"].format(
            chat_name=chat_title,
            # disconnect is builtin command, should not be shown
            commands=", ".join(f"<code>/{cmd}</code>" for cmd in connected_data["command"] if cmd != "disconnect"),
        )
    else:
        text = ""

    text += strings["select_chat_to_connect"]
    markup = InlineKeyboardMarkup(inline_keyboard=[])
    for chat_id in reversed(connected_data["history"][-3:]):
        chat = await db.chat_list.find_one({"chat_id": chat_id})
        markup.inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text=chat["chat_title"],
                    callback_data=ConnectToChatCb(chat_id=chat_id).pack(),
                )
            ]
        )

    await message.reply(text, reply_markup=markup)


# Callback for prev. function
@dp.callback_query(ConnectToChatCb.filter())
async def connect_chat_keyboard_cb(message: Message, callback_data: ConnectToChatCb, **kwargs):
    chat_id = int(callback_data.chat_id)
    chat = await db.chat_list.find_one({"chat_id": chat_id})
    await def_connect_chat(message.message, message.from_user.id, chat_id, chat["chat_title"], edit=True)


# In pm with args - connect to chat by arg
@register(router, cmds="connect", has_args=True, only_pm=True)
@flags.help(description=l_("Connected to the chat by its ID."), args={"state": IntArg(l_("Chat ID"))})
@get_chat_dec()
@get_strings_dec("connections")
async def connect_to_chat_from_arg(message: Message, chat, strings):
    user_id = message.from_user.id
    chat_id = chat["chat_id"]

    arg = get_arg(message)
    if arg.startswith("-"):
        chat_id = int(arg)

    if not chat_id:
        await message.reply(strings["cant_find_chat_use_id"])
        return

    await def_connect_chat(message, user_id, chat_id, chat["chat_title"])


@register(router, cmds="disconnect", only_pm=True)
@flags.help(description=l_("Disconnects the PM from connected chat."))
@get_strings_dec("connections")
async def disconnect_from_chat_direct(message: Message, strings):
    if (data := await get_connection_data(message.from_user.id)) and "chat_id" in data:
        chat = await db.chat_list.find_one({"chat_id": data["chat_id"]})
        user_id = message.from_user.id
        await set_connected_chat(user_id, None)
        await message.reply(strings["disconnected"].format(chat_name=chat["chat_title"]))


@register(router, cmds="allowusersconnect", is_admin=True)
@flags.help(
    description=l_("Sets whatever normal users (non admins) are allowed to connect"),
    args={"state": BooleanArg(l_("New state"))},
)
@get_strings_dec("connections")
@chat_connection(admin=True, only_groups=True)
async def allow_users_to_connect(message: Message, strings, chat):
    chat_id = chat["chat_id"]
    arg = get_arg(message).lower()
    if not arg:
        status = strings["enabled"]
        data = await db.chat_connection_settings.find_one({"chat_id": chat_id})
        if data and "allow_users_connect" in data and data["allow_users_connect"] is False:
            status = strings["disabled"]
        await message.reply(strings["chat_users_connections_info"].format(status=status, chat_name=chat["chat_title"]))
        return
    enable = ("enable", "on", "ok", "yes")
    disable = ("disable", "off", "no")
    if arg in enable:
        r_bool = True
        status = strings["enabled"]
    elif arg in disable:
        r_bool = False
        status = strings["disabled"]
    else:
        await message.reply(strings["bad_arg_bool"])
        return

    await db.chat_connection_settings.update_one(
        {"chat_id": chat_id}, {"$set": {"allow_users_connect": r_bool}}, upsert=True
    )
    await message.reply(strings["chat_users_connections_cng"].format(status=status, chat_name=chat["chat_title"]))


@register(router, CommandStart(), only_pm=True)
@get_strings_dec("connections")
@chat_connection()
async def connected_start_state(message: Message, strings, chat):
    key = "sophie_connected_start_state:" + str(message.from_user.id)
    if redis.get(key):
        await message.reply(strings["pm_connected"].format(chat_name=chat["chat_title"]))
        redis.delete(key)


BUTTONS.update({"connect": "btn_connect_start"})


@register(router, CommandStart(deep_link=True, magic=F.args.regexp(r"btn_connect_start")), allow_kwargs=True)
@get_strings_dec("connections")
async def connect_start(message: Message, strings, regexp=None, **kwargs):
    args = get_args_str(message).split("_")

    # In case if button have arg it will be used. # TODO: Check chat_id, parse chat nickname.
    arg = args[3]

    if arg.startswith("-") or arg.isdigit():
        chat = await db.chat_list.find_one({"chat_id": int(arg)})
    elif arg.startswith("@"):
        chat = await db.chat_list.find_one({"chat_nick": arg.lower()})
    else:
        await message.reply(strings["cant_find_chat_use_id"])
        return

    await def_connect_chat(message, message.from_user.id, chat["chat_id"], chat["chat_title"])


@dp.callback_query(F.data == "anon_conn_cb")
async def connect_anon_admins(event: CallbackQuery):
    if not await is_user_admin(event.message.chat.id, event.from_user.id):
        return

    if event.message.chat.id not in (data := await db.user_list.find_one({"user_id": event.from_user.id}))["chats"]:
        await db.user_list.update_one({"_id": data["_id"]}, {"$addToSet": {"chats": event.message.chat.id}})
    return await event.answer(url=await get_start_link(f"btn_connect_start_{event.message.chat.id}"))
