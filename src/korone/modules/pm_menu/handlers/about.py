# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from contextlib import suppress

from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.enums import ChatType
from hydrogram.errors import MessageNotModified
from hydrogram.types import CallbackQuery, InlineKeyboardButton, Message
from magic_filter import F

from korone import __version__, constants
from korone.decorators import router
from korone.filters import Command
from korone.modules.pm_menu.callback_data import PMMenu, PMMenuCallback
from korone.utils.i18n import gettext as _

LICENSE_URL = f"{constants.GITHUB_URL}/blob/main/LICENSE"
HYDROGRAM_URL = "https://github.com/hydrogram/hydrogram"
PYTHON_URL = "https://www.python.org/"
MTPROTO_URL = "https://core.telegram.org/mtproto"
PRIVACY_POLICY_URL = f"{constants.DOCS_URL}/en/latest/privacy.html"


@router.message(Command("about"))
@router.callback_query(PMMenuCallback.filter(F.menu == PMMenu.About))
async def about_command(client: Client, update: Message | CallbackQuery) -> None:
    python_link = f"<a href='{PYTHON_URL}'>Python</a>"
    hydrogram_link = f"<a href='{HYDROGRAM_URL}'>Hydrogram</a>"
    mtproto_link = f"<a href='{MTPROTO_URL}'>Telegram MTProto API</a>"
    license_link = f"<a href='{LICENSE_URL}'>BSD 3-Clause</a>"

    text = _(
        "Korone is a comprehensive and cutting-edge Telegram bot that offers a wide range "
        "of features to enhance your Telegram experience. Designed to be versatile, "
        "adaptable, and highly efficient, it leverages the power of {python} and is built on "
        "the {hydrogram} framework, utilizing the {mtproto}.\n\n"
        "This open source project is licensed under the {license} license, with the "
        "source code available on GitHub.\n\n"
        "Version: <code>{version}</code>"
    ).format(
        python=python_link,
        hydrogram=hydrogram_link,
        mtproto=mtproto_link,
        license=license_link,
        version=__version__,
    )

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=_("📦 GitHub"), url=constants.GITHUB_URL)
    keyboard.button(text=_("📚 Channel"), url=constants.TELEGRAM_URL)
    keyboard.button(text=_("🔒 Privacy Policy"), url=PRIVACY_POLICY_URL)
    keyboard.adjust(2)

    message = update.message if isinstance(update, CallbackQuery) else update
    if message.chat.type == ChatType.PRIVATE:
        keyboard.row(
            InlineKeyboardButton(
                text=_("⬅️ Back"), callback_data=PMMenuCallback(menu=PMMenu.Start).pack()
            )
        )

    reply_markup = keyboard.as_markup()

    if isinstance(update, Message):
        await update.reply(text, reply_markup=reply_markup, disable_web_page_preview=True)
        return

    if isinstance(update, CallbackQuery):
        with suppress(MessageNotModified):
            await update.message.edit(
                text, reply_markup=reply_markup, disable_web_page_preview=True
            )
