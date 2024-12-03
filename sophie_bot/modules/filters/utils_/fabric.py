from abc import ABC, abstractmethod
from typing import Any

from aiogram.types import Message
from ass_tg.types.base_abc import ArgFabric

from sophie_bot.utils.i18n import LazyProxy


class FilterActionABC(ABC):
    name: str

    args: ArgFabric
    data: dict[str, Any]

    title: LazyProxy

    @property
    def description(self) -> LazyProxy:
        raise NotImplementedError

    @abstractmethod
    async def handle(self, message: Message):
        pass


class FilterActions(list[FilterActionABC]):
    def find(self, name: str) -> FilterActionABC:
        for action in self:
            if action.name == name:
                return action
        raise ValueError(f"No action with name {name} found")


class ReplyFilterAction(FilterActionABC):
    name = "reply"
