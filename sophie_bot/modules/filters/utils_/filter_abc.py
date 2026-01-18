from abc import ABC
from dataclasses import dataclass
from typing import Any, Generic, Optional, TypeVar

from aiogram import Router
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import InlineKeyboardMarkup, Message
from stfu_tg.doc import Element

from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.utils.i18n import LazyProxy

T = TypeVar("T")


ALL_FILTER_ACTIONS: dict[str, "FilterActionABC"] = {}


class FilterActionSetupHandlerABC(SophieMessageHandler, ABC):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (lambda _: False,)

    @classmethod
    def register(cls, router: Router):
        # We don't need to register filter action handlers in the dispatcher, since it's going to be executed from other handlers
        pass


@dataclass
class FilterActionSetting:
    name_id: str
    title: LazyProxy
    icon: str
    handler: type[FilterActionSetupHandlerABC]


class FilterActionSetupTryAgainException(Exception):
    pass


class FilterActionABC(ABC, Generic[T]):
    name: str

    data: dict[str, Any]

    icon: str
    title: LazyProxy

    settings: tuple[FilterActionSetting, ...]

    @classmethod
    def setup_message(cls) -> tuple[Element | str, InlineKeyboardMarkup]:
        """
        Starts the optional filter action data setup process.
        Can return None, which means that Filter does not need any additional configuration.
        """
        raise NotImplementedError

    @classmethod
    async def setup_confirm(cls, message: Message, data: dict[str, Any]) -> Optional[T]:
        """
        Validates and prepares the filter action data.
        Can raise FilterActionSetupTryAgainException
        """
        return None

    @staticmethod
    def description(data: T) -> Element | str:
        raise NotImplementedError

    async def handle(self, message: Message, data: dict, filter_data: T):
        pass
