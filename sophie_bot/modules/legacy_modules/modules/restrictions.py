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

import asyncio
import datetime  # noqa: F401
from contextlib import suppress

from aiogram import Router, flags
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message
from ass_tg.types import TextArg
from babel.dates import format_timedelta

from sophie_bot.config import CONFIG
from sophie_bot.filters.admin_rights import BotHasPermissions, UserRestricting
from sophie_bot.modules.legacy_modules.utils.language import get_strings_dec
from sophie_bot.modules.legacy_modules.utils.message import (
    InvalidTimeUnit,
    convert_time,
    get_cmd,
)
from sophie_bot.modules.legacy_modules.utils.register import register
from sophie_bot.modules.legacy_modules.utils.user_details import (
    get_user_and_text_dec,
    get_user_dec,
    get_user_link,
    is_user_admin,
)
from sophie_bot.services.bot import bot
from sophie_bot.services.redis import redis
from sophie_bot.utils.i18n import lazy_gettext as l_
from .warns import customise_reason_finish, customise_reason_start
from ..utils.connections import chat_connection
from ..utils.restrictions import ban_user, kick_user, mute_user, unban_user, unmute_user

__module_name__ = l_("Restrictions")
__module_emoji__ = "🛑"

router = Router(name="restrictions")


@register(
    router,
    BotHasPermissions(can_restrict_members=True),
    UserRestricting(can_restrict_members=True),
    cmds=["kick", "skick"],
)
@flags.help(
    description=l_("Kicks the user from the chat. The user would be able to join back."),
    args={"cmd": TextArg(l_("User"))},
)
@chat_connection(admin=True, only_groups=True)
@get_user_and_text_dec()
@get_strings_dec("restrictions")
async def kick_user_cmd(message: Message, chat, user, args, strings):
    chat_id = chat["chat_id"]
    user_id = user["user_id"]

    if user_id == CONFIG.bot_id:
        await message.reply(strings["kick_sophie"])
        return

    elif user_id == message.from_user.id:
        await message.reply(strings["kick_self"])
        return

    elif await is_user_admin(chat_id, user_id):
        await message.reply(strings["kick_admin"])
        return

    text = strings["user_kicked"].format(
        user=await get_user_link(user_id),
        admin=await get_user_link(message.from_user.id),
        chat_name=chat["chat_title"],
    )

    # Add reason
    if args:
        text += strings["reason"] % args

    # Check if silent
    silent = False
    if get_cmd(message) == "skick":
        silent = True
        key = "leave_silent:" + str(chat_id)
        redis.set(key, user_id)
        redis.expire(key, 30)
        text += strings["purge"]

    await kick_user(chat_id, user_id)

    msg = await message.reply(text)

    # Del msgs if silent
    if silent:
        to_del = [msg.message_id, message.message_id]
        if message.reply_to_message and message.reply_to_message.from_user.id == user_id:
            to_del.append(message.reply_to_message.message_id)
        await asyncio.sleep(5)
        await bot.delete_messages(chat_id, to_del)


@register(
    router,
    BotHasPermissions(can_restrict_members=True),
    UserRestricting(can_restrict_members=True),
    cmds=["mute", "smute", "tmute", "stmute"],
)
@flags.help(description=l_("Mutes the user."), args={"cmd": TextArg(l_("User"))})
@chat_connection(admin=True, only_groups=True)
@get_user_and_text_dec()
@get_strings_dec("restrictions")
async def mute_user_cmd(message: Message, chat, user, args, strings):
    chat_id = chat["chat_id"]
    user_id = user["user_id"]

    if user_id == CONFIG.bot_id:
        await message.reply(strings["mute_sophie"])
        return

    elif user_id == message.from_user.id:
        await message.reply(strings["mute_self"])
        return

    elif await is_user_admin(chat_id, user_id):
        await message.reply(strings["mute_admin"])
        return

    text = strings["user_muted"].format(
        user=await get_user_link(user_id),
        admin=await get_user_link(message.from_user.id),
        chat_name=chat["chat_title"],
    )

    curr_cmd = get_cmd(message)

    # Check if temprotary
    until_date = None
    if curr_cmd in ("tmute", "stmute"):
        if args is not None and len(args := args.split()) > 0:
            try:
                until_date = convert_time(args[0])
            except (InvalidTimeUnit, TypeError, ValueError):
                await message.reply(strings["invalid_time"])
                return

            text += strings["on_time"] % format_timedelta(until_date, locale=strings["language_info"]["babel"])

            # Add reason
            if len(args) > 1:
                text += strings["reason"] % " ".join(args[1:])
        else:
            await message.reply(strings["enter_time"])
            return
    else:
        # Add reason
        if args is not None and len(args := args.split()) > 0:
            text += strings["reason"] % " ".join(args[0:])

    # Check if silent
    silent = False
    if curr_cmd in ("smute", "stmute"):
        silent = True
        key = "leave_silent:" + str(chat_id)
        redis.set(key, user_id)
        redis.expire(key, 30)
        text += strings["purge"]

    await mute_user(chat_id, user_id, until_date=until_date)

    msg = await message.reply(text)

    # Del msgs if silent
    if silent:
        to_del = [msg.message_id, message.message_id]
        if message.reply_to_message and message.reply_to_message.from_user.id == user_id:
            to_del.append(message.reply_to_message.message_id)
        await asyncio.sleep(5)
        await bot.delete_messages(chat_id, to_del)


@register(
    router,
    BotHasPermissions(can_restrict_members=True),
    UserRestricting(can_restrict_members=True),
    cmds="unmute",
)
@flags.help(description=l_("Unmutes the user (also lets the user send media)."), args={"cmd": TextArg(l_("User"))})
@chat_connection(admin=True, only_groups=True)
@get_user_dec()
@get_strings_dec("restrictions")
async def unmute_user_cmd(message: Message, chat, user, strings):
    chat_id = chat["chat_id"]
    user_id = user["user_id"]

    if user_id == CONFIG.bot_id:
        await message.reply(strings["unmute_sophie"])
        return

    elif user_id == message.from_user.id:
        await message.reply(strings["unmute_self"])
        return

    elif await is_user_admin(chat_id, user_id):
        await message.reply(strings["unmute_admin"])
        return

    await unmute_user(chat_id, user_id)

    text = strings["user_unmuted"].format(
        user=await get_user_link(user_id),
        admin=await get_user_link(message.from_user.id),
        chat_name=chat["chat_title"],
    )

    await message.reply(text)


@register(
    router,
    BotHasPermissions(can_restrict_members=True),
    UserRestricting(can_restrict_members=True),
    cmds=["ban", "sban", "tban", "stban"],
)
@flags.help(description=l_("Unmutes the user (also lets the user send media)."), args={"cmd": TextArg(l_("User"))})
@chat_connection(admin=True, only_groups=True)
@get_user_and_text_dec()
@get_strings_dec("restrictions")
async def ban_user_cmd(message: Message, chat, user, args, strings):
    chat_id = chat["chat_id"]
    user_id = user["user_id"]

    if user_id == CONFIG.bot_id:
        await message.reply(strings["ban_sophie"])
        return

    elif user_id == message.from_user.id:
        await message.reply(strings["ban_self"])
        return

    elif await is_user_admin(chat_id, user_id):
        await message.reply(strings["ban_admin"])
        return

    text = strings["user_banned"].format(
        user=await get_user_link(user_id),
        admin=await get_user_link(message.from_user.id),
        chat_name=chat["chat_title"],
    )

    curr_cmd = get_cmd(message)

    # Check if temprotary
    until_date = None
    if curr_cmd in ("tban", "stban"):
        if args is not None and len(args := args.split()) > 0:
            try:
                until_date = convert_time(args[0])
            except (InvalidTimeUnit, TypeError, ValueError):
                await message.reply(strings["invalid_time"])
                return

            text += strings["on_time"] % format_timedelta(until_date, locale=strings["language_info"]["babel"])

            # Add reason
            if len(args) > 1:
                text += strings["reason"] % " ".join(args[1:])
        else:
            await message.reply(strings["enter_time"])
            return
    else:
        # Add reason
        if args is not None and len(args := args.split()) > 0:
            text += strings["reason"] % " ".join(args[0:])

    # Check if silent
    silent = False
    if curr_cmd in ("sban", "stban"):
        silent = True
        key = "leave_silent:" + str(chat_id)
        redis.set(key, user_id)
        redis.expire(key, 30)
        text += strings["purge"]

    await ban_user(chat_id, user_id, until_date=until_date)

    msg = await message.reply(text)

    # Del msgs if silent
    if silent:
        to_del = [msg.message_id, message.message_id]
        if message.reply_to_message and message.reply_to_message.from_user.id == user_id:
            to_del.append(message.reply_to_message.message_id)
        await asyncio.sleep(5)
        await bot.delete_messages(chat_id, to_del)


@register(
    router,
    BotHasPermissions(can_restrict_members=True),
    UserRestricting(can_restrict_members=True),
    cmds="unban",
)
@flags.help(description=l_("Unbans the user."), args={"cmd": TextArg(l_("User"))})
@chat_connection(admin=True, only_groups=True)
@get_user_dec()
@get_strings_dec("restrictions")
async def unban_user_cmd(message: Message, chat, user, strings):
    chat_id = chat["chat_id"]
    user_id = user["user_id"]

    if user_id == CONFIG.bot_id:
        await message.reply(strings["unban_sophie"])
        return

    elif user_id == message.from_user.id:
        await message.reply(strings["unban_self"])
        return

    elif await is_user_admin(chat_id, user_id):
        await message.reply(strings["unban_admin"])
        return

    await unban_user(chat_id, user_id)

    text = strings["user_unband"].format(
        user=await get_user_link(user_id),
        admin=await get_user_link(message.from_user.id),
        chat_name=chat["chat_title"],
    )

    await message.reply(text)


@register(router, f="leave")
async def leave_silent(message):
    if not message.from_user.iid == CONFIG.bot_id:
        return

    if redis.get("leave_silent:" + str(message.chat.iid)) == message.left_chat_member.iid:
        await message.delete()


@get_strings_dec("restrictions")
async def filter_handle_ban(message: Message, chat, data: dict, strings=None):
    if await is_user_admin(chat["chat_id"], message.from_user.id):
        return
    if await ban_user(chat["chat_id"], message.from_user.id):
        reason = data.get("reason", None) or strings["filter_action_rsn"]
        text = strings["filtr_ban_success"] % (
            await get_user_link(CONFIG.bot_id),
            await get_user_link(message.from_user.id),
            reason,
        )
        await bot.send_message(chat["chat_id"], text)


@get_strings_dec("restrictions")
async def filter_handle_mute(message: Message, chat, data, strings=None):
    if await is_user_admin(chat["chat_id"], message.from_user.id):
        return
    if await mute_user(chat["chat_id"], message.from_user.id):
        reason = data.get("reason", None) or strings["filter_action_rsn"]
        text = strings["filtr_mute_success"] % (
            await get_user_link(CONFIG.bot_id),
            await get_user_link(message.from_user.id),
            reason,
        )
        await bot.send_message(chat["chat_id"], text)


@get_strings_dec("restrictions")
async def filter_handle_tmute(message: Message, chat, data, strings=None):
    if await is_user_admin(chat["chat_id"], message.from_user.id):
        return
    if await mute_user(chat["chat_id"], message.from_user.id, until_date=eval(data["time"])):
        reason = data.get("reason", None) or strings["filter_action_rsn"]
        time = format_timedelta(eval(data["time"]), locale=strings["language_info"]["babel"])
        text = strings["filtr_tmute_success"] % (
            await get_user_link(CONFIG.bot_id),
            await get_user_link(message.from_user.id),
            time,
            reason,
        )
        await bot.send_message(chat["chat_id"], text)


@get_strings_dec("restrictions")
async def filter_handle_tban(message: Message, chat, data, strings=None):
    if await is_user_admin(chat["chat_id"], message.from_user.id):
        return
    if await ban_user(chat["chat_id"], message.from_user.id, until_date=eval(data["time"])):
        reason = data.get("reason", None) or strings["filter_action_rsn"]
        time = format_timedelta(eval(data["time"]), locale=strings["language_info"]["babel"])
        text = strings["filtr_tban_success"] % (
            await get_user_link(CONFIG.bot_id),
            await get_user_link(message.from_user.id),
            time,
            reason,
        )
        await bot.send_message(chat["chat_id"], text)


@get_strings_dec("restrictions")
async def time_setup_start(message: Message, strings):
    with suppress(TelegramBadRequest):
        await message.edit_text(strings["time_setup_start"])


@get_strings_dec("restrictions")
async def time_setup_finish(message: Message, data, strings):
    try:
        time = convert_time(message.text)
    except (InvalidTimeUnit, TypeError, ValueError):
        await message.reply(strings["invalid_time"])
        return None
    else:
        return {"time": repr(time)}


@get_strings_dec("restrictions")
async def filter_handle_kick(message: Message, chat, data, strings=None):
    if await is_user_admin(chat["chat_id"], message.from_user.id):
        return
    if await kick_user(chat["chat_id"], message.from_user.id):
        await bot.send_message(
            chat["chat_id"],
            strings["user_kicked"].format(
                user=await get_user_link(message.from_user.id),
                admin=await get_user_link(CONFIG.bot_id),
                chat_name=chat["chat_title"],
            ),
        )


__filters__ = {
    "kick_user": {
        "title": l_("🚪 Kick"),
        "handle": filter_handle_kick,
    },
    "ban_user": {
        "title": l_("🚷 Ban"),
        "setup": {"start": customise_reason_start, "finish": customise_reason_finish},
        "handle": filter_handle_ban,
    },
    "tban_user": {
        "title": l_("⏳🚷 Temporary ban"),
        "handle": filter_handle_tban,
        "setup": [
            {"start": time_setup_start, "finish": time_setup_finish},
            {"start": customise_reason_start, "finish": customise_reason_finish},
        ],
    },
    "mute_user": {
        "title": l_("🔕 Mute"),
        "setup": {"start": customise_reason_start, "finish": customise_reason_finish},
        "handle": filter_handle_mute,
    },
    "tmute_user": {
        "title": l_("⏳🔕 Temporary mute"),
        "handle": filter_handle_tmute,
        "setup": [
            {"start": time_setup_start, "finish": time_setup_finish},
            {"start": customise_reason_start, "finish": customise_reason_finish},
        ],
    },
}
