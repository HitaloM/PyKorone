from typing import TYPE_CHECKING, Any

from aiogram.filters import BaseFilter

from korone.modules.medias.utils.settings import is_auto_download_enabled
from korone.modules.medias.utils.url import normalize_media_url

if TYPE_CHECKING:
    from collections.abc import Sequence

    from aiogram.types import Message

    from korone.modules.medias.utils.provider_base import MediaProvider


class MediaUrlFilter(BaseFilter):
    def __init__(self, providers: Sequence[type[MediaProvider]], *, check_enabled: bool = True) -> None:
        self.providers = tuple(providers)
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

        selected_provider: type[MediaProvider] | None = None
        urls: list[str] = []
        for provider in self.providers:
            normalized_urls = (normalize_media_url(match.group(0)) for match in provider.pattern.finditer(text))
            urls = list(dict.fromkeys(url for url in normalized_urls if url))
            if urls:
                selected_provider = provider
                break

        if selected_provider is None:
            return False

        if self.check_enabled and not await is_auto_download_enabled(message.chat.id):
            return False

        return {"media_provider": selected_provider, "media_urls": urls}
