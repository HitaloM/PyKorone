from abc import ABC, abstractmethod
from typing import Optional, TypeVar

from aiogram import Router
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.fsm.context import FSMContext
from aiogram.handlers import BaseHandler, BaseHandlerMixin
from aiogram.types import (
    CallbackQuery,
    InaccessibleMessage,
    InputFile,
    InputMediaPhoto,
    Message,
)
from ass_tg.types.base_abc import ArgFabric
from stfu_tg.doc import Element

from sophie_bot import bot
from sophie_bot.middlewares.connections import ChatConnection
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.i18n import gettext as _

T = TypeVar("T")


class SophieBaseHandler(BaseHandler[T], BaseHandlerMixin[T], ABC):
    @property
    def connection(self) -> ChatConnection:
        return self.data["connection"]

    @property
    def state(self) -> FSMContext:
        return self.data["state"]

    @property
    def current_locale(self) -> str:
        return self.data["i18n"].current_locale

    @classmethod
    @abstractmethod
    def register(cls, router: Router):
        pass


class SophieMessageHandler(SophieBaseHandler[Message], ABC):
    @classmethod
    async def handler_args(cls, message: Message | None, data: dict) -> dict[str, ArgFabric]:
        return {}

    @staticmethod
    @abstractmethod
    def filters() -> tuple[CallbackType, ...]:
        pass

    @classmethod
    def register(cls, router: Router):
        flags = {"args": cls.handler_args}

        router.message.register(cls, *cls.filters(), flags=flags)


class SophieCallbackQueryHandler(SophieBaseHandler[CallbackQuery], ABC):
    @staticmethod
    @abstractmethod
    def filters() -> tuple[CallbackType, ...]:
        pass

    @classmethod
    def register(cls, router: Router):
        router.callback_query.register(cls, *cls.filters())

    async def check_for_message(self):
        if not self.event.from_user:
            raise SophieException("Not a user clicked a button")

        if not self.event.message or isinstance(self.event.message, InaccessibleMessage):
            raise SophieException(_("The message is inaccessible. Please write the command again"))


class SophieMessageCallbackQueryHandler(SophieBaseHandler[Message | CallbackQuery], ABC):

    async def answer_media(self, f: InputFile, caption: Optional[str] = None, **kwargs) -> Message | bool:
        if isinstance(self.event, InaccessibleMessage):
            raise SophieException(_("The message is inaccessible. Please write the command again"))
        elif isinstance(self.event, CallbackQuery) and self.event.message:
            return await bot.edit_message_media(
                media=InputMediaPhoto(media=f, caption=caption),
                chat_id=self.event.message.chat.id,
                message_id=self.event.message.message_id,
                **kwargs
            )
        elif isinstance(self.event, Message):
            return await bot.send_photo(chat_id=self.event.chat.id, photo=f, caption=caption, **kwargs)
        else:
            raise ValueError("answer_media: Wrong event type")

    async def answer(self, text: Element | str, **kwargs) -> Message | bool:
        if isinstance(self.event, CallbackQuery) and self.event.message:
            if isinstance(self.event.message, InaccessibleMessage):
                raise SophieException(_("The message is inaccessible. Please write the command again"))

            return await self.event.message.edit_text(str(text), **kwargs)
        elif isinstance(self.event, Message):
            return await self.event.reply(str(text), **kwargs)
        else:
            raise ValueError("answer: Wrong event type")
