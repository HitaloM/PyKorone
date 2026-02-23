from __future__ import annotations

import asyncio
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from korone.config import CONFIG
from korone.logger import get_logger

if TYPE_CHECKING:
    from aiogram import Bot

logger = get_logger(__name__)


async def download_telegram_file(bot: Bot, file_id: str, destination: Path) -> None:
    if CONFIG.botapi_server:
        await logger.adebug(
            "download_telegram_file: trying local Bot API storage", file_id=file_id, destination=str(destination)
        )
        file = await bot.get_file(file_id)
        file_path = getattr(file, "file_path", None)

        if file_path:
            local_path = resolve_local_botapi_file_path(file_path)
            if await asyncio.to_thread(local_path.exists):
                await asyncio.to_thread(shutil.copyfile, local_path, destination)
                await logger.adebug(
                    "download_telegram_file: copied from local Bot API storage",
                    file_id=file_id,
                    source=str(local_path),
                    destination=str(destination),
                )
                return
            await logger.adebug(
                "download_telegram_file: local Bot API file not found, falling back to Telegram download",
                file_id=file_id,
                source=str(local_path),
            )
        else:
            await logger.adebug(
                "download_telegram_file: missing file_path from get_file, falling back", file_id=file_id
            )

    await logger.adebug(
        "download_telegram_file: downloading file via Telegram API", file_id=file_id, destination=str(destination)
    )
    await bot.download(file=file_id, destination=destination)


def resolve_local_botapi_file_path(file_path: str) -> Path:
    candidate = Path(file_path)
    if candidate.is_absolute():
        return candidate

    return Path(CONFIG.botapi_local_storage_root) / file_path.lstrip("/")
