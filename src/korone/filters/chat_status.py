from typing import TYPE_CHECKING

from aiogram.enums import ChatType
from aiogram.filters import Filter

if TYPE_CHECKING:
    from aiogram.types import Chat, TelegramObject


class ChatTypeFilter(Filter):
    __slots__ = ("chat_types",)

    def __init__(self, *chat_types: str | ChatType) -> None:
        self.chat_types = tuple(self._normalize_chat_type(chat_type) for chat_type in chat_types)

    @staticmethod
    def _normalize_chat_type(chat_type: str | ChatType) -> str:
        if isinstance(chat_type, ChatType):
            return chat_type.value
        return str(chat_type)

    async def __call__(self, event: TelegramObject, event_chat: Chat, **kwargs: str | float | bool | None) -> bool:
        return self._normalize_chat_type(event_chat.type) in self.chat_types
