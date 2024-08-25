# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio
import functools
import re

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import HasText, IsAdmin
from korone.handlers.abstract import MessageHandler
from korone.modules.filters.database import get_filters_cache, update_filters_cache
from korone.modules.filters.utils import FilterModel
from korone.modules.filters.utils.parse_buttons.unparse import unparse_buttons
from korone.modules.filters.utils.text import vars_parser


class CheckMsgFilter(MessageHandler):
    @router.message(HasText())
    async def handle(self, client: Client, message: Message) -> None:
        chat_id = message.chat.id

        chat_filters = await get_filters_cache(chat_id) or await update_filters_cache(chat_id)

        if not chat_filters:
            return

        text = message.text or message.caption

        if await IsAdmin(client, message, show_alert=False) and text[1:].startswith((
            "filter",
            "delfilter",
        )):
            return

        compiled_patterns = [
            (filter, re.compile(r"( |^|[^\w])" + re.escape(name) + r"( |$|[^\w])", re.IGNORECASE))
            for filter in chat_filters
            for name in filter.names
        ]

        for filter, pattern in compiled_patterns:
            func = functools.partial(re.search, pattern, text)
            try:
                matched = await asyncio.wait_for(asyncio.to_thread(func), timeout=0.2)
                if matched:
                    await self.send_filter(message, filter)
                    return
            except TimeoutError:
                continue

    @staticmethod
    async def send_filter(message: Message, filter: FilterModel) -> None:
        buttons = unparse_buttons(filter.buttons) if filter.buttons else None
        parsed_text = vars_parser(filter.text, message, message.from_user) if filter.text else None

        if filter.content_type == "text" and parsed_text:
            await message.reply(parsed_text, reply_markup=buttons, disable_web_page_preview=True)
            return

        if not filter.file:
            return

        content_type_methods = {
            "photo": message.reply_photo,
            "video": message.reply_video,
            "audio": message.reply_audio,
            "voice": message.reply_voice,
            "document": message.reply_document,
            "sticker": message.reply_sticker,
            "animation": message.reply_animation,
        }

        if reply_method := content_type_methods.get(filter.content_type):
            if filter.content_type == "sticker":
                await reply_method(filter.file.file_id)
            else:
                await reply_method(
                    filter.file.file_id,
                    caption=parsed_text or "",
                    reply_markup=buttons,
                )
