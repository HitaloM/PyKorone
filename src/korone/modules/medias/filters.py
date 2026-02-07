from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiogram.filters import BaseFilter

from korone.modules.medias.utils.settings import is_auto_download_enabled

if TYPE_CHECKING:
    import re

    from aiogram.types import Message


class MediaUrlFilter(BaseFilter):
    def __init__(self, pattern: re.Pattern[str], *, check_enabled: bool = True) -> None:
        self.pattern = pattern
        self.check_enabled = check_enabled

    async def __call__(self, message: Message) -> bool | dict[str, Any]:
        text = message.text or message.caption or ""
        if not text:
            return False

        urls = [match.group(0) for match in self.pattern.finditer(text)]
        if not urls:
            return False

        if self.check_enabled and not await is_auto_download_enabled(message.chat.id):
            return False

        return {"media_urls": urls}
