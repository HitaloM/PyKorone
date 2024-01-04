# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from hairydogm.i18n import gettext as _
from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client, filters
from hydrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from korone.decorators import on_callback_query, on_message
from korone.handlers.callback_query_handler import CallbackQueryHandler
from korone.handlers.message_handler import MessageHandler
from korone.modules import MODULES


class HelpMessageHandler(MessageHandler):
    @staticmethod
    def build_keyboard() -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardBuilder()
        for module in MODULES.items():
            module_name = module[1]["info"]["name"]
            keyboard.button(text=module_name, callback_data=f"gethelp:{module[0]}")

        keyboard.adjust(3)
        keyboard.row(InlineKeyboardButton(text=_("⬅️ Back"), callback_data="startmenu"))
        return keyboard.as_markup()  # type: ignore

    @staticmethod
    def build_text() -> str:
        return _(
            "Below are buttons for each module. Click on a button to "
            "access a brief documentation on its functionality and usage."
        )

    @on_message(filters.command("help"))
    async def handle(self, client: Client, message: Message) -> None:
        await message.reply_text(
            self.build_text(),
            reply_markup=self.build_keyboard(),
        )


class GetHelpCallbackHandler(CallbackQueryHandler):
    @staticmethod
    def build_keyboard() -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text=_("⬅️ Back"), callback_data="helpmenu")
        return keyboard.as_markup()  # type: ignore

    @staticmethod
    def build_text(module_name: str) -> str:
        module = MODULES[module_name]["info"]
        name = module["name"]
        summary = module["summary"]
        doc = module["doc"]

        return f"<b>{name}</b>\n\n{summary}\n\n{doc}"

    @on_callback_query(filters.regex(r"^gethelp:(.*)"))
    async def handle(self, client: Client, callback: CallbackQuery) -> None:
        if callback.matches is None:
            return

        module: str = callback.matches[0].group(1)
        await callback.message.edit_text(
            text=self.build_text(module),
            reply_markup=self.build_keyboard(),
        )


class BackHelpCallbackHandler(CallbackQueryHandler):
    @on_callback_query(filters.regex(r"^helpmenu$"))
    async def handle(self, client: Client, callback: CallbackQuery) -> None:
        await callback.message.edit_text(
            HelpMessageHandler.build_text(),
            reply_markup=HelpMessageHandler.build_keyboard(),
        )
