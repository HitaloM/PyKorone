from aiogram import types
from aiogram.filters import BaseFilter, Filter
from aiogram.types import Chat, TelegramObject


class ChatTypeFilter(BaseFilter):
    def __init__(self, chat_type: str):
        self.chat_type = chat_type

    async def __call__(self, event: TelegramObject, event_chat: Chat) -> bool:
        return event_chat.type == self.chat_type


class LegacyOnlyPM(Filter):
    key = "only_pm"

    def __init__(self, only_pm):
        self.only_pm = only_pm

    async def __call__(self, message: types.Message):
        if message.from_user.id == message.chat.id:
            return True


class LegacyOnlyGroups(Filter):
    key = "only_groups"

    def __init__(self, only_groups):
        self.only_groups = only_groups

    async def __call__(self, message: types.Message):
        if not message.from_user.id == message.chat.id:
            return True
