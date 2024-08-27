# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from contextlib import suppress

from babel import Locale
from flag import flag
from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.enums import ChatType
from hydrogram.errors import MessageNotModified
from hydrogram.types import CallbackQuery, Message
from magic_filter import F

from korone.decorators import router
from korone.filters import Command
from korone.modules.languages.callback_data import LangMenu, LangMenuCallback
from korone.modules.pm_menu.callback_data import PMMenu, PMMenuCallback
from korone.utils.i18n import get_i18n
from korone.utils.i18n import gettext as _


@router.message(Command("start"))
@router.callback_query(PMMenuCallback.filter(F.menu == PMMenu.Start))
async def start_command(client: Client, event: Message | CallbackQuery) -> None:
    text = _(
        "Hi, I'm Korone! An all-in-one bot. I can help you with lots "
        "of things. Just click on the buttons below to get started."
    )

    current_lang = get_i18n().current_locale
    current_lang_flag = flag(Locale.parse(current_lang).territory or "US")

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=_("ℹ️ About"), callback_data=PMMenuCallback(menu=PMMenu.About))
    keyboard.button(
        text=_("{lang_flag} Language").format(lang_flag=current_lang_flag),
        callback_data=LangMenuCallback(menu=LangMenu.Language),
    )
    keyboard.button(text=_("👮‍♂️ Help"), callback_data=PMMenuCallback(menu=PMMenu.Help))
    keyboard.adjust(2)

    if isinstance(event, Message):
        if event.chat.type != ChatType.PRIVATE:
            await event.reply(_("Hi, I'm Korone!"))
            return

        await event.reply(text, reply_markup=keyboard.as_markup())
        return

    if isinstance(event, CallbackQuery):
        with suppress(MessageNotModified):
            await event.message.edit(text, reply_markup=keyboard.as_markup())
