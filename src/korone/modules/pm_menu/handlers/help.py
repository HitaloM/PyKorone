# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.enums import ChatType
from hydrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from magic_filter import F

from korone.decorators import router
from korone.filters import Command, CommandObject
from korone.handlers.abstract import CallbackQueryHandler, MessageHandler
from korone.modules import MODULES
from korone.modules.pm_menu.callback_data import GetHelpCallback, PMMenuCallback
from korone.utils.i18n import gettext as _


class Help(MessageHandler):
    @staticmethod
    def build_keyboard() -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardBuilder()
        for module in MODULES.items():
            if "info" not in module[1]:
                continue

            module_name = module[1]["info"]["name"]
            keyboard.button(text=module_name, callback_data=GetHelpCallback(module=module[0]))

        keyboard.adjust(3)
        keyboard.row(
            InlineKeyboardButton(
                text=_("⬅️ Back"), callback_data=PMMenuCallback(menu="start").pack()
            )
        )
        return keyboard.as_markup()

    @staticmethod
    def build_text() -> str:
        return _(
            "Below are buttons for each module. Click on a button to "
            "access a brief documentation on its functionality and usage."
        )

    @router.message(Command("help"))
    async def handle(self, client: Client, message: Message) -> None:
        if message.chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text=_("👮‍♂️ Help"), url="https://t.me/PyKoroneBot?start=start")
            await message.reply(
                _("Message me in PM to get help."), reply_markup=keyboard.as_markup()
            )
            return

        command = CommandObject(message).parse()

        text = self.build_text()
        keyboard = self.build_keyboard()
        if query := command.args:
            text = GetHelp().build_text(query)
            if _("Module not found.") in text:
                await message.reply(text)
                return

            keyboard = GetHelp().build_keyboard()

        await message.reply(text, reply_markup=keyboard)


class GetHelp(CallbackQueryHandler):
    @staticmethod
    def build_keyboard() -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text=_("⬅️ Back"), callback_data=PMMenuCallback(menu="help"))
        return keyboard.as_markup()

    @staticmethod
    def build_text(module_name: str) -> str:
        module_name = module_name.lower()
        for module_key, module_info in MODULES.items():
            if "info" not in module_info:
                continue

            if module_name in (module_info["info"]["name"].lower(), module_key.lower()):  # noqa: PLR6201
                name = module_info["info"]["name"]
                summary = module_info["info"]["summary"]
                doc = module_info["info"]["doc"]

                return f"<b>{name}</b>\n\n{summary}\n\n{doc}"

        return _("Module not found.")

    @router.callback_query(GetHelpCallback.filter())
    async def handle(self, client: Client, callback: CallbackQuery) -> None:
        if not callback.data:
            return

        module = GetHelpCallback.unpack(callback.data).module
        await callback.message.edit_text(
            text=self.build_text(module),
            reply_markup=self.build_keyboard(),
        )


class HelpCallbackHandler(CallbackQueryHandler):
    @staticmethod
    @router.callback_query(PMMenuCallback.filter(F.menu == "help"))
    async def handle(client: Client, callback: CallbackQuery) -> None:
        text = Help.build_text()
        keyboard = Help.build_keyboard()

        await callback.message.edit_text(text, reply_markup=keyboard)
