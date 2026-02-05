from typing import TYPE_CHECKING

from aiogram.enums import ChatType
from aiogram.filters import Filter
from aiogram.types import CallbackQuery, Message

from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.types import Chat, TelegramObject
    from babel.support import LazyProxy


class BaseChatTypeFilter(Filter):
    __slots__ = ("notify_on_fail",)

    chat_types: tuple[str, ...] = ()
    fail_message: str | LazyProxy | None = None

    def __init__(self, *, notify_on_fail: bool = False) -> None:
        self.notify_on_fail = notify_on_fail

    async def __call__(self, event: TelegramObject, event_chat: Chat, **kwargs: str | float | bool | None) -> bool:
        if event_chat.type in self.chat_types:
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


class GroupChatFilter(BaseChatTypeFilter):
    chat_types = (ChatType.GROUP.value, ChatType.SUPERGROUP.value)
    fail_message = l_("This command can only be used in groups.")


class PrivateChatFilter(BaseChatTypeFilter):
    chat_types = (ChatType.PRIVATE.value,)
    fail_message = l_("This command can only be used in private chats.")
