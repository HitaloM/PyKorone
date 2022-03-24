# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2022 Amano Team
#
# This file is part of Korone (Telegram Bot)

import html
from contextlib import suppress
from typing import Union

from pyrogram import filters
from pyrogram.errors import MessageNotModified
from pyrogram.types import CallbackQuery, Message

import korone
from korone.korone import Korone
from korone.modules import COMMANDS_HELP
from korone.utils.langs.decorators import use_chat_language


@Korone.on_message(
    filters.cmd(command=r"start", action="Envia a mensagem de inicialização do bot.")
)
@Korone.on_callback_query(filters.regex(r"^start_back$"))
@use_chat_language()
async def start(c: Korone, m: Union[Message, CallbackQuery]):
    lang = m._lang
    if isinstance(m, Message):
        query = m.text.split()
        if len(query) > 1:
            field = query[1]
            query = field.split("_")
            if query[0] == "help":
                module = query[1]
                await help_module(c, m, module)
        else:
            keyboard = []
            text = (lang.start_text).format(
                user=m.from_user.first_name,
                bot_name=c.me.first_name,
                version_code=c.version_code,
            )
            if m.chat.type == "private":
                keyboard.append(
                    [
                        (lang.help_button, "help_cb"),
                        (
                            f"{lang.language_button.format(flag=lang.LANGUAGE_FLAG)}",
                            "language",
                        ),
                    ]
                )
                keyboard.append(
                    [
                        (lang.group_button, "https://t.me/SpamTherapy", "url"),
                        (lang.about_button, "about"),
                    ]
                )
            else:
                keyboard.append(
                    [
                        (
                            lang.for_help_button,
                            f"http://t.me/{c.me.username}?start",
                            "url",
                        )
                    ]
                )
                text += lang.what_i_can_do
            await m.reply_text(
                text,
                reply_markup=c.ikb(keyboard),
            )
    if isinstance(m, CallbackQuery):
        text = (lang.start_text).format(
            user=m.from_user.first_name,
            bot_name=c.me.first_name,
            version_code=c.version_code,
        )
        keyboard = [
            [
                (lang.help_button, "help_cb"),
                (f"{lang.language_button.format(flag=lang.LANGUAGE_FLAG)}", "language"),
            ],
            [
                (lang.group_button, "https://t.me/SpamTherapy", "url"),
                (lang.about_button, "about"),
            ],
        ]
        with suppress(MessageNotModified):
            await m.message.edit_text(text, reply_markup=c.ikb(keyboard))


@Korone.on_message(filters.cmd(r"help (?P<module>.+)"))
@use_chat_language()
async def help_m(c: Korone, m: Message):
    lang = m._lang
    module = m.matches[0]["module"]
    if m.chat.type == "private":
        if module in COMMANDS_HELP.keys() or module in [
            "commands",
            "filters",
            "start",
        ]:
            await help_module(c, m, module)
        else:
            await m.reply_text(lang.module_not_found.format(module_name=module))
    elif module in COMMANDS_HELP.keys():
        keyboard = [
            [
                (
                    lang.go_to_pm,
                    f"https://t.me/{c.me.username}/?start=help_{module}",
                    "url",
                )
            ]
        ]
        await m.reply_text(text=lang.to_see_go_pm, reply_markup=c.ikb(keyboard))
    else:
        keyboard = [[(lang.go_to_pm, f"https://t.me/{c.me.username}/?start", "url")]]
        await m.reply_text(
            text=lang.module_not_exist,
            reply_markup=c.ikb(keyboard),
        )


@Korone.on_message(filters.cmd(command=r"help", action="Envia o menu de ajuda do Bot."))
@Korone.on_callback_query(filters.regex(r"^help_cb$"))
@use_chat_language()
async def help_c(c: Korone, m: Union[Message, CallbackQuery]):
    if isinstance(m, Message) and m.chat.type in ["supergroup", "group"]:
        lang = m._lang
        keyboard = [[(lang.go_to_pm, f"https://t.me/{c.me.username}/?start", "url")]]
        await m.reply_text(lang.to_get_help, reply_markup=c.ikb(keyboard))
    elif isinstance(m, (Message, CallbackQuery)):
        await help_module(c, m)


async def help_module(c: Korone, m: Message, module: str = None):
    is_query = isinstance(m, CallbackQuery)
    lang = m._lang
    text = ""
    keyboard = []
    success = False
    if not module or module == "start":
        keyboard.append(
            [
                (lang.commands_button, "help_commands"),
                (lang.filters_button, "help_filters"),
            ]
        )
        keyboard.append([(lang.back_button, "start_back")])
        text = lang.help_text
        success = True
    elif module in {"commands", "filters"}:
        text = lang.choose_module
        keyboard = [[]]
        index = 0
        for key, value in COMMANDS_HELP.items():
            if module in value and "help" in value and value["help"]:
                if len(keyboard[index]) == 3:
                    index += 1
                    keyboard.append([])
                keyboard[index].append(
                    (
                        value["name"] if "name" in value else key.capitalize(),
                        f"help_{key}",
                    )
                )
        success = True
        keyboard.append([(lang.back_button, "help_start")])
    elif module in COMMANDS_HELP.keys():
        text = lang.module_text.format(module_name=module)
        module = COMMANDS_HELP[module]
        text += f'\n{module["text"]}\n'

        m_type = "commands" if "commands" in module else "filters"
        if len(module[m_type]) > 0:
            text += f'\n<b>{lang.commands_button if m_type == "commands" else lang.filters_button}</b>:'
            for key, value in module[m_type].items():
                action = value["action"]
                if len(action) > 0:
                    regex = ""
                    if m_type == "commands":
                        key = key.replace("$", "")
                        regex = key.split()[0]
                        if "<" in key and ">" in key:
                            left = key[len(regex) :].split("<")[1:]
                            for field in left:
                                regex += " <" + field.split(">")[0] + ">"
                        else:
                            regex = key
                    else:
                        regex = key

                    try:
                        trregex = lang.strings[lang.code][regex + "_filter"]
                    except KeyError:
                        trregex = regex
                    try:
                        traction = lang.strings[lang.code][action + "_help"]
                    except KeyError:
                        traction = action

                    if action == " " and m_type == "filters":
                        text += f"\n  - <code>{html.escape(trregex)}</code>"
                    elif action not in [" ", ""] and m_type == "filters":
                        text += f"\n  - <code>{html.escape(trregex)}</code>: {traction}"
                    else:
                        text += f'\n  - <b>{"/" if m_type == "commands" else ""}{html.escape(regex)}</b>: <i>{traction}</i>'
        success = True
        keyboard.append([(lang.back_button, f"help_{m_type}")])

    kwargs = {}
    if keyboard:
        kwargs["reply_markup"] = c.ikb(keyboard)

    if success:
        with suppress(MessageNotModified):
            await (m.edit_message_text if is_query else m.reply_text)(text, **kwargs)


@Korone.on_callback_query(filters.regex(r"help_(?P<module>.+)"))
@use_chat_language()
async def on_help_callback(c: Korone, cq: CallbackQuery):
    module = cq.matches[0]["module"]
    await help_module(c, cq, module)


@Korone.on_message(
    filters.cmd(
        command=r"about",
        action="Veja algumas informações sobre o bot.",
    )
)
@Korone.on_callback_query(filters.regex(r"^about$"))
@use_chat_language()
async def about_c(c: Korone, m: Union[Message, CallbackQuery]):
    is_callback = isinstance(m, CallbackQuery)
    lang = m._lang
    about = lang.about_text.format(
        bot_name=c.me.first_name,
        source_link=korone.__source__,
        group_link=korone.__community__,
    )
    keyboard = c.ikb([[(lang.back_button, "start_back")]])
    with suppress(MessageNotModified):
        await (m.message.edit_text if is_callback else m.reply_text)(
            about,
            reply_markup=(keyboard if is_callback else None),
            disable_web_page_preview=True,
        )
