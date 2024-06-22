# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>


import asyncio
from io import BytesIO
from typing import BinaryIO
from zipfile import ZipFile

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command
from korone.handlers.abstract import MessageHandler
from korone.utils.i18n import gettext as _


class GetSticker(MessageHandler):
    @staticmethod
    def zip_file(file: BinaryIO, file_name: str) -> BytesIO:
        zip_buffer = BytesIO()

        with ZipFile(zip_buffer, "w") as zip_file:
            file.seek(0)
            file_content = file.read()
            zip_file.writestr(file_name, file_content)

        zip_buffer.seek(0)

        return zip_buffer

    @router.message(Command("getsticker"))
    async def handle(self, client: Client, message: Message) -> None:
        if not message.reply_to_message:
            await message.reply(_("Reply to a sticker."))
            return

        if not message.reply_to_message.sticker:
            await message.reply(_("Reply to a sticker to get it as a file and file ID"))
            return

        sticker_file = await client.download_media(
            message=message.reply_to_message, in_memory=True
        )

        if isinstance(sticker_file, str):
            return

        if not sticker_file:
            await message.reply(_("Failed to download sticker."))
            return

        sticker = message.reply_to_message.sticker

        zip_buffer = await asyncio.to_thread(self.zip_file, sticker_file, f"{sticker.file_name}")

        await message.reply_document(
            document=zip_buffer,
            file_name=f"{sticker.set_name}-{sticker.file_unique_id}.zip",
            caption=f"Sticker ID: {sticker.file_id}",
            force_document=True,
        )
