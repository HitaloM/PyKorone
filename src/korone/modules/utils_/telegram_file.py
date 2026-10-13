import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

from aiogram.types import FSInputFile, InputFile

from korone.config import CONFIG

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from aiogram import Bot


def telegram_upload(bot: Bot, file: InputFile | str) -> InputFile | str:
    """Use server paths only for files visible through the shared storage mount."""
    if not bot.session.api.is_local or not isinstance(file, FSInputFile):
        return file
    # A path upload uses the server's basename; multipart preserves explicit display names.
    if file.filename != Path(file.path).name:
        return file
    path = Path(file.path).resolve()
    if not path.is_relative_to(Path(CONFIG.botapi_local_storage_root).resolve()):
        return file
    return str(bot.session.api.wrap_local_file.to_server(path))


@asynccontextmanager
async def telegram_workspace(*, prefix: str) -> AsyncGenerator[Path]:
    """Own temporary outputs until all operations using them have completed."""
    directory = TemporaryDirectory(prefix=prefix, dir=CONFIG.botapi_upload_root)
    try:
        yield Path(directory.name)
    finally:
        await asyncio.to_thread(directory.cleanup)


async def download_telegram_file(bot: Bot, file_id: str, destination: Path) -> None:
    file = await bot.get_file(
        file_id, request_timeout=CONFIG.media_local_download_timeout_seconds if bot.session.api.is_local else None
    )
    if not file.file_path:
        msg = "Telegram getFile returned no file path"
        raise RuntimeError(msg)
    await bot.download_file(file.file_path, destination=destination)


@asynccontextmanager
async def telegram_file(bot: Bot, file_id: str) -> AsyncGenerator[Path]:
    """Borrow local API files for reading; own downloaded files in public mode."""
    file = await bot.get_file(
        file_id, request_timeout=CONFIG.media_local_download_timeout_seconds if bot.session.api.is_local else None
    )
    if not file.file_path:
        msg = "Telegram getFile returned no file path"
        raise RuntimeError(msg)
    if bot.session.api.is_local:
        path = Path(bot.session.api.wrap_local_file.to_local(file.file_path))
        await asyncio.to_thread(_check_readable, path)
        yield path
    else:
        async with telegram_workspace(prefix="korone-telegram-") as workspace:
            destination = workspace / Path(file.file_path).name
            await bot.download_file(file.file_path, destination=destination)
            yield destination


def _check_readable(path: Path) -> None:
    with path.open("rb"):
        pass
