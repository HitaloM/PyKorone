# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import operator
from datetime import UTC, datetime

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, IsSudo
from korone.utils.logging import LOG_DIR


@router.message(Command("logs", disableable=False) & IsSudo)
async def handle_logs_command(client: Client, message: Message) -> None:
    if not (log_files := list(LOG_DIR.glob("korone.log*"))):
        await message.reply("No log files found.")
        return

    file_times = {file: file.stat().st_mtime for file in log_files}
    match max(file_times.items(), key=operator.itemgetter(1)):
        case (most_recent_file, mtime):
            file_size = round(most_recent_file.stat().st_size / (1024 * 1024), 2)
            timestamp = datetime.fromtimestamp(mtime, UTC).strftime("%Y-%m-%d %H:%M:%S")
            caption = (
                f"<b>📄 Log File</b>\n"
                f"<b>File:</b> <code>{most_recent_file.name}</code>\n"
                f"<b>Size:</b> <code>{file_size} MB</code>\n"
                f"<b>Last Modified:</b> <code>{timestamp} UTC</code>"
            )

    status_message = await message.reply("Uploading log file...")

    try:
        await message.reply_document(
            document=str(most_recent_file),
            caption=caption,
            file_name=most_recent_file.name,
        )
        await status_message.delete()
    except Exception as exc:
        await status_message.edit(f"Error sending log file: {exc!s}")
