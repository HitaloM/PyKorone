from __future__ import annotations

from korone.db.repositories.disabling import DisablingRepository

AUTO_DOWNLOAD_KEY = "medias_autodownload"


async def is_auto_download_enabled(chat_id: int) -> bool:
    disabled = await DisablingRepository.get_disabled(chat_id)
    return AUTO_DOWNLOAD_KEY not in disabled
