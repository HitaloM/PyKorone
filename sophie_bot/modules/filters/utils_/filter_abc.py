from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, Optional, TypeVar

from aiogram import Router
from aiogram.types import InlineKeyboardMarkup, Message
from stfu_tg.doc import Element

from sophie_bot.modules.utils_.base_handler import SophieMessageCallbackQueryHandler
from sophie_bot.utils.i18n import LazyProxy

T = TypeVar("T")


ALL_FILTER_ACTIONS: dict[str, "FilterActionABC"] = {}


class FilterActionSetupHandlerABC(SophieMessageCallbackQueryHandler, ABC):
    @classmethod
    def register(cls, router: Router):
        # We don't need to register filter action handlers in the dispatcher, since it's going to be executed from other handlers
        pass


@dataclass
class FilterActionSetting:
    name_id: str
    title: LazyProxy
    icon: str
    handler: FilterActionSetupHandlerABC


class FilterActionSetupTryAgainException(Exception):
    pass


class FilterActionABC(ABC, Generic[T]):
    name: str

    data: dict[str, Any]

    icon: str
    title: LazyProxy

    settings: tuple[FilterActionSetting, ...]

    @classmethod
    def setup_message(cls) -> Optional[tuple[Element | str, str, InlineKeyboardMarkup]]:
        """
        Starts the optional filter action data setup process.
        Can return None, which means that Filter does not need any additional configuration.
        """
        return None

    @classmethod
    async def setup_confirm(cls, message: Message, data: dict[str, Any]) -> T:
        """
        Validates and prepares the filter action data.
        Can raise FilterActionSetupTryAgainException
        """
        return None

    @classmethod
    def description(cls, data: Optional[Any]) -> Element | str:
        raise NotImplementedError

    async def handle(self, message: Message, data: dict, filter_data: T):
        pass
