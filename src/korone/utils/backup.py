# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from datetime import UTC, datetime
from pathlib import Path

from hydrogram import Client
from hydrogram.types import InputMediaDocument

from korone import constants
from korone.utils.logging import logger


async def do_backup(client: Client, backups_chat: int) -> None:
    date = datetime.now(tz=UTC).strftime("%H:%M:%S - %d/%m/%Y")
    caption = f"Korone Backup\nDate: <code>{date}</code>"

    files = [
        InputMediaDocument(media=constants.DEFAULT_DBFILE_PATH),
        InputMediaDocument(media=Path(client.workdir / str(client.name)).as_posix()),
        InputMediaDocument(media=constants.DEFAULT_CONFIG_PATH, caption=caption),
    ]

    await logger.awarning("Starting backup...")

    try:
        await client.send_media_group(backups_chat, media=files)  # type: ignore
        await logger.awarning("Backup was successful!")
    except Exception:
        await logger.aexception("Something went wrong in the bot backup!")
