from typing import TYPE_CHECKING

from aiogram.filters import Filter

from korone.config import CONFIG

if TYPE_CHECKING:
    from aiogram.types import Message


class IsOwner(Filter):
    __slots__ = ("is_owner",)

    key = "is_owner"

    def __init__(self, *, is_owner: bool) -> None:
        self.is_owner = is_owner

    async def __call__(self, message: Message) -> bool:
        return bool(message.from_user and message.from_user.id == CONFIG.owner_id)


class IsOP(Filter):
    __slots__ = ("is_owner",)

    key = "is_op"

    def __init__(self, *, is_op: bool) -> None:
        self.is_owner = is_op

    async def __call__(self, message: Message) -> bool:
        return bool(message.from_user and message.from_user.id in CONFIG.operators)
