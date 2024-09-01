# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from contextlib import suppress

from babel import Locale
from flag import flag
from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.enums import ChatType
from hydrogram.errors import MessageNotModified
from hydrogram.types import CallbackQuery, InlineKeyboardButton, Message
from magic_filter import F

from korone.decorators import router
from korone.filters import Command
from korone.modules.languages.callback_data import LangMenu, LangMenuCallback
from korone.modules.pm_menu.callback_data import PMMenu, PMMenuCallback
from korone.utils.i18n import get_i18n
from korone.utils.i18n import gettext as _


@router.message(Command("start"))
@router.callback_query(PMMenuCallback.filter(F.menu == PMMenu.Start))
async def start_command(client: Client, update: Message | CallbackQuery) -> None:
    text = _(
        "Hi, I'm Korone! An all-in-one bot. I can help you with lots "
        "of things. Just click on the buttons below to get started."
    )

    current_lang_flag = flag(Locale.parse(get_i18n().current_locale).territory or "US")

    keyboard = (
        InlineKeyboardBuilder()
        .button(text=_("ℹ️ About"), callback_data=PMMenuCallback(menu=PMMenu.About))
        .button(
            text=_("{flag} Language").format(flag=current_lang_flag),
            callback_data=LangMenuCallback(menu=LangMenu.Language),
        )
        .row(
            InlineKeyboardButton(
                text=_("👮‍♂️ Help"), callback_data=PMMenuCallback(menu=PMMenu.Help).pack()
            )
        )
    )

    if isinstance(update, Message):
        if update.chat.type != ChatType.PRIVATE:
            await update.reply(_("Hi, I'm Korone!"))
            return

        await update.reply(text, reply_markup=keyboard.as_markup())
        return

    if isinstance(update, CallbackQuery):
        with suppress(MessageNotModified):
            await update.message.edit(text, reply_markup=keyboard.as_markup())
