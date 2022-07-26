# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

from typing import Union

from pyrogram import filters
from pyrogram.helpers import ikb
from pyrogram.nav import Pagination
from pyrogram.types import CallbackQuery, Message

from korone.bot import Korone
from korone.modules.utils.languages import (
    LANGUAGES,
    get_chat_lang,
    get_string,
    get_strings_dec,
)
from korone.utils.modules import HELPABLE


@Korone.on_message(filters.cmd("start"))
@Korone.on_callback_query(filters.regex(r"^start$"))
@get_strings_dec("pm_menu")
async def start(bot: Korone, union: Union[Message, CallbackQuery], strings):
    is_callback = isinstance(union, CallbackQuery)
    message = union.message if is_callback else union

    keyboard = ikb([[(strings["help_button"], "list_commands 0")]])
    await (message.edit_text if is_callback else message.reply_text)(
        strings["start_text"], reply_markup=keyboard
    )


@Korone.on_message(filters.cmd("help"))
@Korone.on_callback_query(filters.regex(r"^list_commands (?P<page>\d+)"))
@get_strings_dec("pm_menu")
async def help_menu(bot: Korone, union: Union[Message, CallbackQuery], strings):
    is_callback = isinstance(union, CallbackQuery)
    message = union.message if is_callback else union
    page = int(union.matches[0]["page"]) if is_callback else 0

    item_format = "info_command {} {}"
    page_format = "list_commands {}"

    lang_code = await get_chat_lang(message.chat.id)
    chat_lang = LANGUAGES[lang_code]["STRINGS"]
    layout = Pagination(
        [*HELPABLE],
        item_data=lambda module, page: item_format.format(module, page),
        item_title=lambda module, page: chat_lang[module]["module_name"],
        page_data=lambda page: page_format.format(page),
    )

    buttons = layout.create(page, columns=2, lines=7)
    buttons.append([(strings["back"], "start")])

    await (message.edit_text if is_callback else message.reply_text)(
        strings["help_text"],
        reply_markup=ikb(buttons),
    )


@Korone.on_callback_query(filters.regex(r"^info_command (?P<module>.+) (?P<page>\d+)"))
@get_strings_dec("pm_menu")
async def help_module(bot: Korone, callback: CallbackQuery, strings):
    module = callback.matches[0]["module"]
    page = int(callback.matches[0]["page"])
    if module not in HELPABLE:
        await callback.answer(
            strings["module_not_found"],
            show_alert=True,
            cache_time=60,
        )
        return

    try:
        help_text = await get_string(callback.from_user.id, module, f"{module}_help")
    except KeyError:
        await callback.answer(
            strings["unavailable_mod_help"],
            show_alert=True,
            cache_time=60,
        )
        return

    keyboard = ikb([[(strings["back"], f"list_commands {page}")]])
    await callback.message.edit_text(help_text, reply_markup=keyboard)


__help__ = True
