from typing import TYPE_CHECKING

from aiogram.enums import ChatType
from aiogram.filters import Filter
from aiogram.types import CallbackQuery, Message

if TYPE_CHECKING:
    from aiogram.types import Chat, TelegramObject
    from babel.support import LazyProxy


class ChatTypeFilter(Filter):
    __slots__ = ("chat_types", "fail_message", "notify_on_fail")

    def __init__(
        self, *chat_types: str | ChatType, notify_on_fail: bool = False, fail_message: str | LazyProxy | None = None
    ) -> None:
        self.chat_types = tuple(self._normalize_chat_type(chat_type) for chat_type in chat_types)
        self.notify_on_fail = notify_on_fail
        self.fail_message = fail_message

    @staticmethod
    def _normalize_chat_type(chat_type: str | ChatType) -> str:
        if isinstance(chat_type, ChatType):
            return chat_type.value
        return str(chat_type)

    async def __call__(self, event: TelegramObject, event_chat: Chat, **kwargs: str | float | bool | None) -> bool:
        matches = self._normalize_chat_type(event_chat.type) in self.chat_types
        if matches:
            return True

        if self.notify_on_fail and self.fail_message:
            await self._notify(event)

        return False

    async def _notify(self, event: TelegramObject) -> None:
        message = self.fail_message
        if not message:
            return

        if isinstance(event, Message):
            await event.reply(str(message))
            return

        if isinstance(event, CallbackQuery):
            await event.answer(str(message), show_alert=True)
