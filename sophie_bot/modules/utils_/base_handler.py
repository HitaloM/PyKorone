from abc import ABC, abstractmethod
from typing import TypeVar

from aiogram.dispatcher.event.handler import CallbackType
from aiogram.handlers import BaseHandler, BaseHandlerMixin
from aiogram.types import CallbackQuery, Message

from sophie_bot.middlewares.connections import ChatConnection

T = TypeVar("T")


class SophieBaseHandler(BaseHandler[T], BaseHandlerMixin[T], ABC):
    def connection(self) -> ChatConnection:
        return self.data["connection"]

    @staticmethod
    @abstractmethod
    def filters() -> tuple[CallbackType, ...]:
        pass


class SophieMessageHandler(SophieBaseHandler[Message], ABC):
    pass


class SophieCallbackQueryHandler(SophieBaseHandler[CallbackQuery], ABC):
    pass


# class SophieMessageCallbackQueryHandler(SophieBaseHandler[Message | CallbackQuery], ABC):
#     async def answer(self, text: Element | str, **kwargs):
#         if isinstance(self.event, CallbackQuery):
#             await self.event.message.edit_text(str(text), **kwargs)
#         else:
#             await self.event.reply(str(text), **kwargs)
