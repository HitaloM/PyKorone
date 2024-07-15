# Copyright (C) 2018 - 2020 MrYacha. All rights reserved. Source code available under the AGPL.
# Copyright (C) 2019 Aiogram
# Copyright (C) 2020 Jeepeo

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

from contextlib import suppress

from aiogram import F
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    TelegramObject,
)

from sophie_bot import CONFIG, dp
from sophie_bot.modules.legacy_modules.utils.disable import disableable_dec
from sophie_bot.modules.legacy_modules.utils.language import get_strings_dec
from sophie_bot.modules.legacy_modules.utils.register import register

from .language import select_lang_keyboard


@register(cmds="start", no_args=True, only_groups=True)
@disableable_dec("start")
@get_strings_dec("pm_menu")
async def start_group_cmd(message: Message, strings):
    await message.reply(strings["start_hi_group"])


@register(cmds="start", no_args=True, only_pm=True)
async def start_cmd(message):
    await get_start_func(message)


@get_strings_dec("pm_menu")
async def get_start_func(event: TelegramObject, strings, edit=False):
    msg = event.message if hasattr(event, "message") else event
    task = msg.edit_text if edit else msg.reply
    buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=strings["btn_lang"], callback_data="lang_btn")],
            [InlineKeyboardButton(text=strings["btn_help"], url=CONFIG.wiki_link)],
            [
                InlineKeyboardButton(text=strings["btn_chat"], url=CONFIG.support_link),
                InlineKeyboardButton(text=strings["btn_channel"], url=CONFIG.news_channel),
            ],
            [
                InlineKeyboardButton(
                    text=strings["btn_add"],
                    url=f"https://telegram.me/{CONFIG.username}?startgroup=true",
                )
            ],
        ]
    )
    # Handle error when user click the button 2 or more times simultaneously
    with suppress(TelegramBadRequest):
        await task(strings["start_hi"], reply_markup=buttons)


@dp.callback_query(F.data == "lang_btn")
async def set_lang_cb(event):
    await select_lang_keyboard(event.message, edit=True)


@dp.callback_query(F.data == "go_to_start")
async def back_btn(event):
    await get_start_func(event, edit=True)


@register(cmds="help")
@disableable_dec("help")
@get_strings_dec("pm_menu")
async def help_cmd(message: Message, strings):
    button = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=strings["click_btn"], url="https://sophiebot.rocks/")]]
    )
    await message.reply(strings["help_header"], reply_markup=button)
