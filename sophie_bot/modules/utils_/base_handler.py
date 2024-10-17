from abc import ABC, abstractmethod
from typing import TypeVar

from aiogram.dispatcher.event.handler import CallbackType
from aiogram.handlers import BaseHandler, BaseHandlerMixin
from aiogram.types import CallbackQuery, InaccessibleMessage, Message

from sophie_bot.middlewares.connections import ChatConnection
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.i18n import gettext as _

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
    async def check_for_message(self):
        if not self.event.from_user:
            raise SophieException("Not a user clicked a button")

        if not self.event.message or isinstance(self.event.message, InaccessibleMessage):
            raise SophieException(_("The message is inaccessible. Please write the command again"))


# class SophieMessageCallbackQueryHandler(SophieBaseHandler[Message | CallbackQuery], ABC):
#     async def answer(self, text: Element | str, **kwargs):
#         if isinstance(self.event, CallbackQuery):
#             await self.event.message.edit_text(str(text), **kwargs)
#         else:
#             await self.event.reply(str(text), **kwargs)
