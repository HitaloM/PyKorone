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
from korone.modules.filters.database import list_filters
from korone.modules.filters.utils import FilterModel


class CheckMsgFilter(MessageHandler):
    @router.message(HasText())
    async def handle(self, client: Client, message: Message) -> None:
        chat_id = message.chat.id

        chat_filters = await list_filters(chat_id)
        if not chat_filters:
            return

        text = message.text or message.caption

        if await IsAdmin(client, message, show_alert=False) and (
            text[1:].startswith("filter") or text[1:].startswith("delfilter")
        ):
            return

        for filter in chat_filters:
            for name in filter.names:
                pattern = re.compile(
                    r"( |^|[^\w])" + re.escape(name) + r"( |$|[^\w])", re.IGNORECASE
                )
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
        if filter.content_type == "text" and filter.text:
            await message.reply(filter.text)
            return

        if not filter.file_id:
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

        reply_method = content_type_methods.get(filter.content_type)
        if reply_method:
            if filter.content_type == "sticker":
                await reply_method(filter.file_id)
            else:
                await reply_method(filter.file_id, caption=filter.text or "")
