from abc import ABC
from typing import TypeVar

from aiogram.handlers import BaseHandler, BaseHandlerMixin
from aiogram.types import CallbackQuery, Message

from sophie_bot.middlewares.connections import ChatConnection

T = TypeVar("T")


class SophieBaseHandler(BaseHandler[T], BaseHandlerMixin[T], ABC):
    def connection(self) -> ChatConnection:
        return self.data["connection"]


class SophieMessageHandler(SophieBaseHandler[Message], ABC):
    pass


class SophieCallbackQueryHandler(SophieBaseHandler[CallbackQuery], ABC):
    pass
