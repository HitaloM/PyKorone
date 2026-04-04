from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiogram.filters import BaseFilter

from korone.modules.medias.utils.settings import is_auto_download_enabled
from korone.modules.medias.utils.url import normalize_media_url

if TYPE_CHECKING:
    import re

    from aiogram.types import Message


class MediaUrlFilter(BaseFilter):
    def __init__(self, pattern: re.Pattern[str], *, check_enabled: bool = True) -> None:
        self.pattern = pattern
        self.check_enabled = check_enabled

    @staticmethod
    def _is_url_command(text: str) -> bool:
        if not text:
            return False

        command_token = text.lstrip().split(maxsplit=1)[0]
        if not command_token.startswith("/"):
            return False

        command = command_token[1:].split("@", maxsplit=1)[0].casefold()
        return command == "url"

    async def __call__(self, message: Message) -> bool | dict[str, Any]:
        text = message.text or message.caption or ""
        if not text:
            return False

        if self._is_url_command(text):
            return False

        normalized_urls = (normalize_media_url(match.group(0)) for match in self.pattern.finditer(text))
        urls = list(dict.fromkeys(url for url in normalized_urls if url))

        if not urls:
            return False

        if self.check_enabled and not await is_auto_download_enabled(message.chat.id):
            return False

        return {"media_urls": urls}
