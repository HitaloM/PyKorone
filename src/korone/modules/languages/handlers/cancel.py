# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio
from contextlib import suppress

from hydrogram import Client
from hydrogram.errors import BadRequest, MessageDeleteForbidden
from hydrogram.types import CallbackQuery
from magic_filter import F

from korone.decorators import router
from korone.modules.languages.callback_data import LangMenuCallback
from korone.utils.i18n import gettext as _


@router.callback_query(LangMenuCallback.filter(F.menu == "cancel"))
async def language_cancel_callback(client: Client, callback: CallbackQuery):
    message = callback.message

    await message.edit(
        _(
            "Changing language was canceled, you can change language again "
            "by using /language command."
        )
    )

    await asyncio.sleep(5)
    with suppress(MessageDeleteForbidden, BadRequest):
        await message.reply_to_message.delete()
        await message.delete()
