# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

from typing import Union

from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.helpers import ikb
from pyrogram.nav import Pagination
from pyrogram.types import CallbackQuery, Message

from korone.bot import Korone
from korone.modules.utils.languages import (
    get_chat_lang,
    get_chat_lang_info,
    get_string,
    get_string_sync,
    get_strings_dec,
)
from korone.modules.utils.messages import get_args
from korone.utils.modules import HELPABLE


@Korone.on_message(filters.cmd("start"))
@Korone.on_callback_query(filters.regex(r"^start$"))
@get_strings_dec("pm_menu")
async def start(bot: Korone, union: Union[Message, CallbackQuery], strings):
    is_callback = isinstance(union, CallbackQuery)
    message = union.message if is_callback else union

    if not is_callback and message.chat.type in (
        ChatType.GROUP,
        ChatType.SUPERGROUP,
    ):
        await message.reply_text(strings["start_group"])
        return

    lang_info = await get_chat_lang_info(message.chat.id)
    keyboard = ikb(
        [
            [
                (strings["about_button"], "about"),
                (f"{lang_info['flag']} {strings['language_button']}", "language"),
            ],
            [(strings["help_button"], "help-menu 0")],
        ]
    )
    await (message.edit_text if is_callback else message.reply_text)(
        strings["start_text"].format(
            user=union.from_user.first_name,
            bot_name=bot.name.capitalize(),
            short_hash=bot.version,
            version_code=bot.version_code,
        ),
        disable_web_page_preview=True,
        reply_markup=keyboard,
    )


@Korone.on_message(filters.cmd("help"))
@Korone.on_callback_query(filters.regex(r"^help-menu (?P<page>\d+)"))
@get_strings_dec("pm_menu")
async def help_menu(bot: Korone, union: Union[Message, CallbackQuery], strings):
    is_callback = isinstance(union, CallbackQuery)
    message = union.message if is_callback else union

    if not is_callback and message.chat.type in (
        ChatType.GROUP,
        ChatType.SUPERGROUP,
    ):
        keyboard = ikb(
            [[(strings["pm_button"], f"https://t.me/{bot.me.username}/?start", "url")]]
        )
        await message.reply_text(strings["help_in_pm"], reply_markup=keyboard)
        return

    page = int(union.matches[0]["page"]) if is_callback else 0
    args = get_args(message)
    if args:
        await help_module(bot, message, args)
        return

    item_format = "help-module {} {}"
    page_format = "help-menu {}"

    lang_code = await get_chat_lang(message.chat.id)
    layout = Pagination(
        [*HELPABLE],
        item_data=item_format.format,
        item_title=lambda module, page: get_string_sync(
            message.chat.id, lang_code, module, "module_name"
        ),
        page_data=page_format.format,
    )

    buttons = layout.create(page, columns=2, lines=7)
    buttons.append([(strings["back_button"], "start")])

    await (message.edit_text if is_callback else message.reply_text)(
        strings["help_text"],
        disable_web_page_preview=True,
        reply_markup=ikb(buttons),
    )


@Korone.on_callback_query(filters.regex(r"^help-module (?P<module>.+) (?P<page>\d+)"))
@get_strings_dec("pm_menu")
async def help_module(
    bot: Korone, union: Union[Message, CallbackQuery], strings, module: str = None
):
    is_callback = isinstance(union, CallbackQuery)
    message = union.message if is_callback else union
    module = union.matches[0]["module"] if is_callback else module
    page = int(union.matches[0]["page"]) if is_callback else 0
    if module not in HELPABLE:
        if is_callback:
            await union.answer(
                strings["module_not_found"],
                show_alert=True,
                cache_time=60,
            )
        else:
            await message.reply_text(strings["module_not_found"])
        return

    try:
        module_name = await get_string(union.from_user.id, module, "module_name")
        module_help = await get_string(union.from_user.id, module, "module_help")
    except KeyError:
        if is_callback:
            await union.answer(
                strings["unavailable_mod_help"],
                show_alert=True,
                cache_time=60,
            )
        else:
            await message.reply_text(strings["unavailable_mod_help"])
        return

    keyboard = ikb([[(strings["back_button"], f"help-menu {page}")]])
    await (message.edit_text if is_callback else message.reply_text)(
        strings["helpable_text"].format(
            module_name=module_name, module_help=module_help
        ),
        disable_web_page_preview=True,
        reply_markup=keyboard,
    )


@Korone.on_message(filters.cmd(r"about$"))
@Korone.on_callback_query(filters.regex(r"^about$"))
@get_strings_dec("pm_menu")
async def about(bot: Korone, union: Union[CallbackQuery, Message], strings):
    is_callback = isinstance(union, CallbackQuery)
    message = union.message if is_callback else union

    keyboard = [
        [
            (strings["github_button"], "https://github.com/AmanoTeam/PyKorone", "url"),
            (strings["channel_button"], "https://t.me/HitaloProjects", "url"),
        ]
    ]

    is_private = await filters.private(bot, message)
    if is_private:
        keyboard.append(
            [
                (strings["back_button"], "start"),
            ],
        )

    await (message.edit_text if is_callback else message.reply_text)(
        strings["about_text"].format(
            bot_name=bot.me.first_name,
            version=f"<a href='https://github.com/AmanoTeam/PyKorone/commit/{bot.version}'>{bot.version}</a>",
            version_code=bot.version_code,
        ),
        disable_web_page_preview=True,
        reply_markup=ikb(keyboard),
    )
