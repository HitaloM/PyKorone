from aiogram.filters import Filter
from aiogram.types import Message

from korone.config import CONFIG


class IsOwner(Filter):
    __slots__ = ("is_owner",)

    key = "is_owner"

    def __init__(self, is_owner):
        self.is_owner = is_owner

    async def __call__(self, message: Message):
        if message.from_user and message.from_user.id == CONFIG.owner_id:
            return True


class IsOP(Filter):
    __slots__ = ("is_owner",)

    key = "is_op"

    def __init__(self, is_op):
        self.is_owner = is_op

    async def __call__(self, message: Message):
        if message.from_user and message.from_user.id in CONFIG.operators:
            return True
