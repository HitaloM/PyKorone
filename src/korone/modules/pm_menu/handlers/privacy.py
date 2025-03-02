# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from korone import constants
from korone.decorators import router
from korone.filters import Command
from korone.utils.i18n import gettext as _


@router.message(Command("privacy"))
async def privacy_command(client: Client, message: Message) -> None:
    text = _(
        "The privacy policy is available for review in the documentation. "
        "Click the button below to start reading."
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(text=_("Privacy Policy"), url=constants.PRIVACY_POLICY_URL)]
    ])

    await message.reply(text, reply_markup=keyboard)
