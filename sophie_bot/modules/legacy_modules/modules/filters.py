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
import functools
import random
import re
from contextlib import suppress
from string import printable

import regex
from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from async_timeout import timeout
from bson.objectid import ObjectId
from pymongo import UpdateOne

from sophie_bot import bot, dp
from sophie_bot.modules.legacy_modules.modules import LOADED_LEGACY_MODULES
from sophie_bot.modules.legacy_modules.utils.connections import (
    chat_connection,
    get_connected_chat,
)
from sophie_bot.modules.legacy_modules.utils.language import get_string, get_strings_dec
from sophie_bot.modules.legacy_modules.utils.message import get_args_str, need_args_dec
from sophie_bot.modules.legacy_modules.utils.register import register
from sophie_bot.modules.legacy_modules.utils.user_details import (
    is_chat_creator,
    is_user_admin,
)
from sophie_bot.services.db import db
from sophie_bot.services.redis import redis
from sophie_bot.utils.logger import log

router = Router(name="filters")


class FilterActionCb(CallbackData, prefix="filter_action_cp"):
    filter_id: str


class FilterRemoveCb(CallbackData, prefix="filter_remove_cp"):
    id: str


class FilterDelallYesCb(CallbackData, prefix="filter_delall_yes_cb"):
    chat_id: int


FILTERS_ACTIONS = {}


class NewFilter(StatesGroup):
    handler = State()
    setup = State()


async def update_handlers_cache(chat_id):
    redis.delete(f"filters_cache_{chat_id}")
    filters = db.filters.find({"chat_id": chat_id})
    handlers = []
    async for filter in filters:
        handler = filter["handler"]
        if handler in handlers:
            continue

        handlers.append(handler)
        redis.lpush(f"filters_cache_{chat_id}", handler)

    return handlers


@register(
    router,
)
async def check_msg(message: Message):
    chat = await get_connected_chat(message, only_groups=True)
    if "err_msg" in chat or message.chat.type == "private":
        return

    chat_id = chat["chat_id"]

    log.debug(f"Enforcing filter check in {chat_id}.")

    if not (filters := redis.lrange(f"filters_cache_{chat_id}", 0, -1)):
        filters = await update_handlers_cache(chat_id)

    if len(filters) == 0:
        return

    text = message.text or message.caption
    if not text:
        return

    # Workaround to disable all filters if admin want to remove filter
    if await is_user_admin(chat_id, message.from_user.id):
        if text[1:].startswith("addfilter") or text[1:].startswith("delfilter"):
            return

    for handler in filters:  # type: str
        if handler.startswith("re:"):
            func = functools.partial(regex.search, handler.replace("re:", "", 1), text, timeout=0.1)
        else:
            # TODO: Remove this (handler.replace(...)). kept for backward compatibility
            func = functools.partial(
                re.search,
                re.escape(handler).replace("(+)", "(.*)"),
                text,
                flags=re.IGNORECASE,
            )

        try:
            async with timeout(0.1):
                matched = func()
        except (asyncio.TimeoutError, TimeoutError):
            continue

        if matched:
            # We can have few filters with same handler, that's why we create a new loop.
            filters = db.filters.find({"chat_id": chat_id, "handler": handler})
            async for filter in filters:
                action = filter["action"]
                await FILTERS_ACTIONS[action]["handle"](message, chat, filter)


@register(router, cmds=["addfilter", "newfilter"], is_admin=True)
@need_args_dec()
@chat_connection(only_groups=True, admin=True)
@get_strings_dec("filters")
async def add_handler(message: Message, chat, strings):
    # filters doesn't support anon admins
    if message.from_user.id == 1087968824:
        return await message.reply(strings["anon_detected"])

    handler = get_args_str(message)

    if handler.startswith("re:"):
        pattern = handler
        random_text_str = "".join(random.choice(printable) for i in range(50))
        try:
            regex.match(pattern, random_text_str, timeout=0.2)
        except TimeoutError:
            await message.reply(strings["regex_too_slow"])
            return
    else:
        handler = handler.lower()

    text = strings["adding_filter"].format(handler=handler, chat_name=chat["chat_title"])

    buttons = InlineKeyboardMarkup(inline_keyboard=[])
    for action in FILTERS_ACTIONS.items():
        filter_id = action[0]
        data = action[1]

        buttons.inline_keyboard.append([
            InlineKeyboardButton(
                text=await get_string(chat["chat_id"], data["title"]["module"], data["title"]["string"]),
                callback_data=FilterActionCb(filter_id=filter_id).pack(),
            )
        ])
    buttons.inline_keyboard.append([InlineKeyboardButton(text=strings["cancel_btn"], callback_data="cancel")])

    user_id = message.from_user.id
    chat_id = chat["chat_id"]
    redis.set(f"add_filter:{user_id}:{chat_id}", handler)
    if handler is not None:
        await message.reply(text, reply_markup=buttons)


async def save_filter(message: Message, data, strings):
    if await db.filters.find_one(data):
        # prevent saving duplicate filter
        await message.reply("Duplicate filter!")
        return

    await db.filters.insert_one(data)
    await update_handlers_cache(data["chat_id"])
    await message.reply(strings["saved"])


@dp.callback_query(FilterActionCb.filter())
@chat_connection(only_groups=True, admin=True)
@get_strings_dec("filters")
async def register_action(event, chat, strings, callback_data: FilterActionCb, state: FSMContext, **kwargs):
    if not await is_user_admin(event.message.chat.id, event.from_user.id):
        return await event.answer("You are not admin to do this")
    filter_id = callback_data.filter_id
    action = FILTERS_ACTIONS[filter_id]

    user_id = event.from_user.id
    chat_id = chat["chat_id"]

    handler = redis.get(f"add_filter:{user_id}:{chat_id}")

    if not handler:
        return await event.answer("Something went wrong! Please try again!", show_alert=True)

    data = {"chat_id": chat_id, "handler": handler, "action": filter_id}

    if "setup" in action:
        await state.set_state(NewFilter.setup)
        setup_co = len(action["setup"]) - 1 if type(action["setup"]) is list else 0

        await state.update_data({
            "data": data,
            "filter_id": filter_id,
            "setup_co": setup_co,
            "setup_done": 0,
            "msg_id": event.message.message_id,
        })

        if setup_co > 0:
            await action["setup"][0]["start"](event.message)
        else:
            await action["setup"]["start"](event.message)
        return

    await save_filter(event.message, data, strings)


@register(router, state=NewFilter.setup, f="any", is_admin=True, allow_kwargs=True)
@chat_connection(only_groups=True, admin=True)
@get_strings_dec("filters")
async def setup_end(message: Message, chat, strings, state: FSMContext, **kwargs):
    state_data = await state.get_data()

    with suppress(TelegramBadRequest):
        await bot.delete_message(message.chat.id, state_data.get("msg_id"))

    action = FILTERS_ACTIONS[state_data["filter_id"]]

    curr_step = state_data.get("setup_done", 0)

    func = action["setup"][curr_step]["finish"] if type(action["setup"]) is list else action["setup"]["finish"]
    if not bool(a := await func(message, state_data["data"])):
        await state.clear()
        return

    state_data["data"].update(a)

    if state_data["setup_co"] > 0:
        await action["setup"][curr_step + 1]["start"](message)
        state_data["setup_co"] -= 1
        state_data["setup_done"] += 1
        await state.set_data(state_data)
        return

    await state.clear()
    await save_filter(message, state_data["data"], strings)


@register(router, cmds=["filters", "listfilters"])
@chat_connection(only_groups=True)
@get_strings_dec("filters")
async def list_filters(message: Message, chat, strings):
    text = strings["list_filters"].format(chat_name=chat["chat_title"])

    filters = db.filters.find({"chat_id": chat["chat_id"]})
    filters_text = ""
    async for filter in filters:
        filters_text += f"- {filter['handler']}: {filter['action']}\n"

    if not filters_text:
        await message.reply(strings["no_filters_found"].format(chat_name=chat["chat_title"]))
        return

    await message.reply(text + filters_text)


@register(router, cmds="delfilter", is_admin=True)
@need_args_dec()
@chat_connection(only_groups=True, admin=True)
@get_strings_dec("filters")
async def del_filter(message: Message, chat, strings):
    handler = get_args_str(message)
    chat_id = chat["chat_id"]
    filters = await db.filters.find({"chat_id": chat_id, "handler": handler}).to_list(9999)
    if not filters:
        await message.reply(strings["no_such_filter"].format(chat_name=chat["chat_title"]))
        return

    # Remove filter in case if we found only 1 filter with same header
    filter = filters[0]
    if len(filters) == 1:
        await db.filters.delete_one({"_id": filter["_id"]})
        await update_handlers_cache(chat_id)
        await message.reply(strings["del_filter"].format(handler=filter["handler"]))
        return

    # Build keyboard row for select which exactly filter user want to remove
    buttons = InlineKeyboardMarkup(inline_keyboard=[])
    text = strings["select_filter_to_remove"].format(handler=handler)
    for filter in filters:
        action = FILTERS_ACTIONS[filter["action"]]
        buttons.inline_keyboard.append([
            InlineKeyboardButton(
                # If module's filter support custom del btn names else just show action name
                text=("" + action["del_btn_name"](message, filter) if "del_btn_name" in action else filter["action"]),
                callback_data=FilterRemoveCb(id=str(filter["_id"])).pack(),
            )
        ])

    await message.reply(text, reply_markup=buttons)


@dp.callback_query(FilterRemoveCb.filter())
@chat_connection(only_groups=True, admin=True)
@get_strings_dec("filters")
async def del_filter_cb(event, chat, strings, callback_data: FilterRemoveCb, **kwargs):
    if not await is_user_admin(event.message.chat.id, event.from_user.id):
        return await event.answer("You are not admin to do this")
    filter_id = ObjectId(callback_data.id)
    filter = await db.filters.find_one({"_id": filter_id})
    await db.filters.delete_one({"_id": filter_id})
    await update_handlers_cache(chat["chat_id"])
    await event.message.edit_text(strings["del_filter"].format(handler=filter["handler"]))
    return


@register(router, cmds=["delfilters", "delallfilters"])
@get_strings_dec("filters")
async def delall_filters(message: Message, strings: dict):
    if not await is_chat_creator(message, message.chat.id, message.from_user.id):
        return await message.reply(strings["not_chat_creator"])
    buttons = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text=strings["confirm_yes"],
                callback_data=FilterDelallYesCb(chat_id=message.chat.id).pack(),
            ),
            InlineKeyboardButton(text=strings["confirm_no"], callback_data="filter_delall_no_cb"),
        ]]
    )
    return await message.reply(strings["delall_header"], reply_markup=buttons)


@dp.callback_query(FilterRemoveCb.filter())
@get_strings_dec("filters")
async def delall_filters_yes(event: CallbackQuery, strings: dict, callback_data: dict, **_):
    if not await is_chat_creator(event, chat_id := int(callback_data["chat_id"]), event.from_user.id):
        return False
    result = await db.filters.delete_many({"chat_id": chat_id})
    await update_handlers_cache(chat_id)
    return await event.message.edit_text(strings["delall_success"].format(count=result.deleted_count))


@dp.callback_query(F.data == "filter_delall_no_cb")
@get_strings_dec("filters")
async def delall_filters_no(event: CallbackQuery, strings: dict):
    if not await is_chat_creator(event, event.message.chat.id, event.from_user.id):
        return False
    await event.message.delete()


async def __before_serving__(loop):
    log.debug("Adding filters actions")
    for module in LOADED_LEGACY_MODULES:
        if not getattr(module, "__filters__", None):
            continue

        module_name = module.__name__.split(".")[-1]
        log.debug(f"Adding filter action from {module_name} module")
        for data in module.__filters__.items():
            FILTERS_ACTIONS[data[0]] = data[1]


async def __export__(chat_id):
    data = []
    filters = db.filters.find({"chat_id": chat_id})
    async for filter in filters:
        del filter["_id"], filter["chat_id"]
        if "time" in filter:
            filter["time"] = str(filter["time"])
        data.append(filter)

    return {"filters": data}


async def __import__(chat_id, data):
    new = []
    for filter in data:
        new.append(
            UpdateOne(
                {
                    "chat_id": chat_id,
                    "handler": filter["handler"],
                    "action": filter["action"],
                },
                {"$set": filter},
                upsert=True,
            )
        )
    await db.filters.bulk_write(new)
    await update_handlers_cache(chat_id)
