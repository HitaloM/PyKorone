# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import contextlib
from datetime import UTC, datetime
from io import BytesIO

import aiofiles
from hydrogram import Client
from hydrogram.errors import MessageDeleteForbidden
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, IsSudo
from korone.utils.logging import LOG_DIR


@router.message(Command("logs", disableable=False) & IsSudo)
async def handle_logs_command(client: Client, message: Message) -> None:
    log_files = list(LOG_DIR.glob("korone.log*"))
    if not log_files:
        await message.reply("No log files found.")
        return

    most_recent_file = max(log_files, key=lambda f: f.stat().st_mtime)
    file_size = round(most_recent_file.stat().st_size / (1024 * 1024), 2)
    timestamp = datetime.fromtimestamp(most_recent_file.stat().st_mtime, UTC).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    caption = (
        f"<b>📄 Log File</b>\n"
        f"<b>File:</b> <code>{most_recent_file.name}</code>\n"
        f"<b>Size:</b> <code>{file_size} MB</code>\n"
        f"<b>Last Modified:</b> <code>{timestamp} UTC</code>"
    )

    status_message = await message.reply("Uploading log file...")

    try:
        async with aiofiles.open(most_recent_file, "rb") as file:
            file_buffer = BytesIO(await file.read())
            file_buffer.seek(0)

        await message.reply_document(
            document=file_buffer,
            caption=caption,
            file_name=most_recent_file.name,
        )

        with contextlib.suppress(MessageDeleteForbidden):
            await status_message.delete()

    except Exception as exc:
        await status_message.edit(f"Error sending log file: {exc}")
