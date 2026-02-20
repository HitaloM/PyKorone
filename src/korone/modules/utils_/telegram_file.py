from __future__ import annotations

import asyncio
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from korone.config import CONFIG

if TYPE_CHECKING:
    from aiogram import Bot


async def download_telegram_file(bot: Bot, file_id: str, destination: Path) -> None:
    if CONFIG.botapi_server:
        file = await bot.get_file(file_id)
        file_path = getattr(file, "file_path", None)

        if file_path:
            local_path = resolve_local_botapi_file_path(file_path)
            if await asyncio.to_thread(local_path.exists):
                await asyncio.to_thread(shutil.copyfile, local_path, destination)
                return

    await bot.download(file=file_id, destination=destination)


def resolve_local_botapi_file_path(file_path: str) -> Path:
    candidate = Path(file_path)
    if candidate.is_absolute():
        return candidate

    return Path(CONFIG.botapi_local_storage_root) / file_path.lstrip("/")
