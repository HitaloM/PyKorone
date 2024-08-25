# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from contextlib import suppress

from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.enums import ChatType
from hydrogram.errors import MessageNotModified
from hydrogram.types import CallbackQuery, InlineKeyboardButton, Message
from magic_filter import F

from korone import constants
from korone.decorators import router
from korone.filters import Command
from korone.modules.pm_menu.callback_data import PMMenuCallback
from korone.utils.i18n import gettext as _


@router.message(Command("help"))
@router.callback_query(PMMenuCallback.filter(F.menu == "help"))
async def help_command(client: Client, update: Message | CallbackQuery) -> None:
    text = _(
        "You can get help by reading the documentation, where you'll get an overview of the "
        "bot and how to use it to its full potential. Click the button below to start reading."
    )

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=_("Documentation"), url=constants.DOCS_URL)

    message = update.message if isinstance(update, CallbackQuery) else update
    if message.chat.type == ChatType.PRIVATE:
        keyboard.row(
            InlineKeyboardButton(
                text=_("⬅️ Back"), callback_data=PMMenuCallback(menu="start").pack()
            )
        )

    reply_markup = keyboard.as_markup()

    if isinstance(update, Message):
        await message.reply(text, reply_markup=reply_markup)
    elif isinstance(update, CallbackQuery):
        with suppress(MessageNotModified):
            await message.edit(text, reply_markup=reply_markup)
