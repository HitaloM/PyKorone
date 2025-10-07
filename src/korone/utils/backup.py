# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from datetime import UTC, datetime

from anyio import Path
from hydrogram import Client
from hydrogram.types import InputMediaDocument

from korone import constants
from korone.utils.logging import get_logger

logger = get_logger(__name__)


async def do_backup(client: Client, backups_chat: int) -> None:
    date = datetime.now(tz=UTC).strftime("%H:%M:%S - %d/%m/%Y")
    caption = f"Korone Backup\nDate: <code>{date}</code>"

    session_path = Path(client.workdir) / f"{client.name}.session"

    files = [
        InputMediaDocument(media=constants.DEFAULT_DBFILE_PATH),
        InputMediaDocument(media=session_path.as_posix()),
        InputMediaDocument(media=constants.DEFAULT_CONFIG_PATH, caption=caption),
    ]

    await logger.awarning("Starting backup...")

    try:
        await client.send_media_group(backups_chat, media=files)  # type: ignore
        await logger.awarning("Backup was successful!")
    except Exception as error:
        await logger.aexception("Something went wrong in the bot backup!", exc_info=error)
