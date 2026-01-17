# Copyright (C) 2018 - 2020 MrYacha. All rights reserved. Source code available under the AGPL.
# Copyright (C) 2019 Aiogram
from aiogram import Router, flags
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from stfu_tg import Code, Template

from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.modules.legacy_modules.utils.language import (
    LANGUAGES,
    change_chat_lang,
    get_chat_lang_info,
    get_strings,
    get_strings_dec,
)
from sophie_bot.modules.legacy_modules.utils.message import get_arg
from sophie_bot.modules.legacy_modules.utils.register import register
from sophie_bot.services.bot import dp
from sophie_bot.services.db import db
from sophie_bot.utils.i18n import lazy_gettext as l_

__module_name__ = l_("Language")
__module_emoji__ = "🌍"


router = Router(name="language")


class SelectLangCb(CallbackData, prefix="select_lang_cb"):
    lang: str
    back_btn: bool


class TranslatorsLangCb(CallbackData, prefix="translators_lang_cb"):
    lang: str


@register(router, cmds="lang", user_admin=True, no_args=True)
@flags.help(description=l_("Asks for the new language for the chat."))
async def select_lang_cmd(message):
    await select_lang_keyboard(message)


@get_strings_dec("language")
async def select_lang_keyboard(message: Message, strings, edit=False):
    markup = InlineKeyboardMarkup(inline_keyboard=[])
    task = message.reply if edit is False else message.edit_text

    lang_info = await get_chat_lang_info(message.chat.id)

    if message.chat.type == "private":
        text = strings["your_lang"].format(lang=lang_info["flag"] + " " + lang_info["babel"].display_name)
        text += strings["select_pm_lang"]

    # TODO: Connected chat lang info

    else:
        text = strings["chat_lang"].format(lang=lang_info["flag"] + " " + lang_info["babel"].display_name)
        text += strings["select_chat_lang"]

    for lang in LANGUAGES.values():
        lang_info = lang["language_info"]
        markup.inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text=lang_info["flag"] + " " + lang_info["babel"].display_name,
                    callback_data=SelectLangCb(
                        lang=lang_info["code"], back_btn=False if edit is False else True
                    ).pack(),
                )
            ]
        )

    markup.inline_keyboard.append(
        [InlineKeyboardButton(text=strings["crowdin_btn"], url="https://crowdin.com/project/sophiebot")]
    )
    if edit:
        markup.inline_keyboard.append([InlineKeyboardButton(text=strings["back"], callback_data="go_to_start")])

    await task(text, reply_markup=markup)


async def change_lang(message: Message, lang, e=False, back_btn=False):
    chat_id = message.chat.id
    await change_chat_lang(chat_id, lang)

    strings = await get_strings(chat_id, "language")

    lang_info = LANGUAGES[lang]["language_info"]

    text = strings["lang_changed"].format(lang_name=lang_info["flag"] + " " + lang_info["babel"].display_name)
    text += strings["help_us_translate"]

    markup = InlineKeyboardMarkup(inline_keyboard=[])

    if "translators" in lang_info:
        markup.inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text=strings["see_translators"],
                    callback_data=TranslatorsLangCb(lang=lang).pack(),
                )
            ]
        )

    if back_btn == "True":
        # Callback_data converts boolean to str
        markup.inline_keyboard.append([InlineKeyboardButton(text=strings["back"], callback_data="go_to_start")])

    if e:
        await message.edit_text(text, reply_markup=markup, disable_web_page_preview=True)
    else:
        await message.reply(text, reply_markup=markup, disable_web_page_preview=True)


@register(router, cmds="lang", user_admin=True, has_args=True)
@flags.help(exclude=True)
@get_strings_dec("language")
async def select_lang_msg(message: Message, strings):
    lang = get_arg(message).lower()

    if lang not in LANGUAGES:
        await message.reply(strings["not_supported_lang"])
        return

    await change_lang(message, lang)


@dp.callback_query(SelectLangCb.filter(), UserRestricting(admin=True))
async def select_lang_callback(query, callback_data: SelectLangCb, **kwargs):
    lang = callback_data.lang
    back_btn = callback_data.back_btn
    await change_lang(query.message, lang, e=True, back_btn=back_btn)


async def __stats__():
    return Template("{num} legacy languages loaded.", num=Code(len(LANGUAGES)))


async def __export__(chat_id):
    lang = await get_chat_lang_info(chat_id)

    return {"language": lang["code"]}


async def __import__(chat_id, data):
    if data not in LANGUAGES:
        return
    await db.lang.update_one({"chat_id": chat_id}, {"$set": {"lang": data}}, upsert=True)
