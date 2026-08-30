from typing import TYPE_CHECKING, Any

from aiogram.filters import BaseFilter

from korone.modules.medias.settings import is_auto_download_enabled

if TYPE_CHECKING:
    from aiogram.types import Message

    from korone.modules.medias.registry import ProviderRegistry


class MediaUrlFilter(BaseFilter):
    def __init__(self, registry: ProviderRegistry) -> None:
        self._registry = registry

    async def __call__(self, message: Message) -> bool | dict[str, Any]:
        text = message.text or message.caption or ""
        if not text:
            return False

        request = self._registry.match(text)
        if request is None:
            return False

        if not await is_auto_download_enabled(message.chat.id):
            return False

        return {"media_request": request}
