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
        actual_is_owner = bool(message.from_user and message.from_user.id == CONFIG.owner_id)
        return actual_is_owner is self.is_owner


class IsOP(Filter):
    __slots__ = ("is_op",)

    key = "is_op"

    def __init__(self, *, is_op: bool) -> None:
        self.is_op = is_op

    async def __call__(self, message: Message) -> bool:
        actual_is_op = bool(message.from_user and message.from_user.id in CONFIG.operators)
        return actual_is_op is self.is_op
