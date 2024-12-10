from aiogram import types
from aiogram.enums import ChatType
from aiogram.filters import Filter
from aiogram.types import Chat, TelegramObject


class ChatTypeFilter(Filter):
    def __init__(self, *chat_types: str | ChatType):
        self.chat_types = chat_types

    async def __call__(self, event: TelegramObject, event_chat: Chat, **kwargs) -> bool:
        return event_chat.type in self.chat_types


class LegacyOnlyPM(Filter):
    key = "only_pm"

    def __init__(self, only_pm):
        self.only_pm = only_pm

    async def __call__(self, message: types.Message) -> bool:
        if not message.from_user or not message.chat:
            return False

        return message.from_user.id == message.chat.id


class LegacyOnlyGroups(Filter):
    key = "only_groups"

    def __init__(self, only_groups):
        self.only_groups = only_groups

    async def __call__(self, message: types.Message) -> bool:
        if not message.from_user or not message.chat:
            return False

        return message.from_user.id != message.chat.id
