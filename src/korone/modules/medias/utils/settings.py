from __future__ import annotations

from korone.db.repositories.disabling import DisablingRepository

AUTO_DOWNLOAD_KEY = "medias_autodownload"


async def is_auto_download_enabled(chat_id: int) -> bool:
    disabled = await DisablingRepository.get_disabled(chat_id)
    return AUTO_DOWNLOAD_KEY not in disabled


async def set_auto_download_enabled(chat_id: int, *, enabled: bool) -> None:
    disabled = await DisablingRepository.get_disabled(chat_id)

    if enabled:
        if AUTO_DOWNLOAD_KEY not in disabled:
            return
        disabled = [cmd for cmd in disabled if cmd != AUTO_DOWNLOAD_KEY]
        await DisablingRepository.set_disabled(chat_id, disabled)
        return

    if AUTO_DOWNLOAD_KEY in disabled:
        return

    await DisablingRepository.set_disabled(chat_id, [*disabled, AUTO_DOWNLOAD_KEY])
