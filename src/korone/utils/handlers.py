from abc import ABC, abstractmethod
from typing import Any, Optional, TypeVar, cast

from aiogram import Router
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.fsm.context import FSMContext
from aiogram.handlers import BaseHandler, BaseHandlerMixin
from aiogram.types import CallbackQuery, InaccessibleMessage, InputFile, InputMediaPhoto, Message
from ass_tg.types.base_abc import ArgFabric
from stfu_tg.doc import Element

from korone import bot
from korone.middlewares.chat_context import ChatContext
from korone.modules.utils_.reply_or_edit import reply_or_edit
from korone.utils.exception import KoroneException
from korone.utils.i18n import gettext as _

T = TypeVar("T")


class KoroneBaseHandler(BaseHandler[T], BaseHandlerMixin[T], ABC):
    @property
    def chat(self) -> ChatContext:
        return self.data["chat"]

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


class KoroneMessageHandler(KoroneBaseHandler[Message], ABC):
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


class KoroneCallbackQueryHandler(KoroneBaseHandler[CallbackQuery], ABC):
    @staticmethod
    @abstractmethod
    def filters() -> tuple[CallbackType, ...]:
        pass

    @classmethod
    def register(cls, router: Router):
        router.callback_query.register(cls, *cls.filters())

    @property
    def callback_data(self):
        return self.data["callback_data"]

    async def check_for_message(self):
        if not self.event.from_user:
            raise KoroneException("Not a user clicked a button")

        if not self.event.message or isinstance(self.event.message, InaccessibleMessage):
            raise KoroneException(_("The message is inaccessible. Please write the command again"))

    async def edit_text(self, text: Element | str, **kwargs):
        await self.check_for_message()
        message = cast(Message, self.event.message)
        await message.edit_text(str(text), **kwargs)


class KoroneMessageCallbackQueryHandler(KoroneBaseHandler[Message | CallbackQuery], ABC):
    @property
    def message(self) -> Message:
        if isinstance(self.event, Message):
            msg = self.event
        else:
            msg = getattr(self.event, "message", None)

        if not msg:
            raise KoroneException("No message in the event")
        if isinstance(msg, InaccessibleMessage):
            raise KoroneException(_("The message is inaccessible. Please write the command again"))
        if not isinstance(msg, Message):
            raise KoroneException(_("The message is inaccessible. Please write the command again"))
        return msg

    @property
    def callback_data(self) -> Optional[Any]:
        return self.data.get("callback_data")

    async def answer_media(self, f: InputFile, caption: Optional[str] = None, **kwargs) -> Message | bool:
        if isinstance(self.event, InaccessibleMessage):
            raise KoroneException(_("The message is inaccessible. Please write the command again"))
        elif isinstance(self.event, CallbackQuery) and self.event.message:
            return await bot.edit_message_media(
                media=InputMediaPhoto(media=f, caption=caption),
                chat_id=self.event.message.chat.id,
                message_id=self.event.message.message_id,
                **kwargs,
            )
        elif isinstance(self.event, Message):
            return await bot.send_photo(chat_id=self.event.chat.id, photo=f, caption=caption, **kwargs)
        else:
            raise ValueError("answer_media: Wrong event type")

    async def answer(self, text: Element | str, **kwargs) -> Message | bool:
        return await reply_or_edit(self.event, text, **kwargs)
