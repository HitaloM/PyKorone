from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, TypeVar, cast

from aiogram.handlers import BaseHandler, BaseHandlerMixin
from aiogram.types import CallbackQuery, InaccessibleMessage, InputMediaPhoto, Message

from korone import bot
from korone.modules.utils_.reply_or_edit import reply_or_edit
from korone.utils.exception import KoroneError

if TYPE_CHECKING:
    from aiogram import Router
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.filters.callback_data import CallbackData
    from aiogram.fsm.context import FSMContext
    from aiogram.types import InputFile
    from ass_tg.types.base_abc import ArgFabric
    from stfu_tg.doc import Element

    from korone.middlewares.chat_context import ChatContext

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
    def register(cls, router: Router) -> None:
        pass


class KoroneMessageHandler(KoroneBaseHandler[Message], ABC):
    @classmethod
    async def handler_args(cls, message: Message | None, data: dict[str, Any]) -> dict[str, ArgFabric]:
        return {}

    @staticmethod
    @abstractmethod
    def filters() -> tuple[CallbackType, ...]:
        pass

    @classmethod
    def register(cls, router: Router) -> None:
        flags = {"args": cls.handler_args}

        router.message.register(cls, *cls.filters(), flags=flags)


class KoroneCallbackQueryHandler(KoroneBaseHandler[CallbackQuery], ABC):
    @staticmethod
    @abstractmethod
    def filters() -> tuple[CallbackType, ...]:
        pass

    @classmethod
    def register(cls, router: Router) -> None:
        router.callback_query.register(cls, *cls.filters())

    @property
    def callback_data(self) -> CallbackData | str:
        return self.data["callback_data"]

    async def check_for_message(self) -> None:
        if not self.event.from_user:
            raise KoroneError.user_context_unavailable()

        if not self.event.message or isinstance(self.event.message, InaccessibleMessage):
            raise KoroneError.inaccessible_message()

    async def edit_text(self, text: Element | str, **kwargs: object) -> None:
        await self.check_for_message()
        message = cast("Message", self.event.message)
        await message.edit_text(str(text), **cast("Any", kwargs))


class KoroneMessageCallbackQueryHandler(KoroneBaseHandler[Message | CallbackQuery], ABC):
    @property
    def message(self) -> Message:
        msg = self.event if isinstance(self.event, Message) else getattr(self.event, "message", None)

        if not msg:
            raise KoroneError.inaccessible_message()
        if isinstance(msg, InaccessibleMessage):
            raise KoroneError.inaccessible_message()
        if not isinstance(msg, Message):
            raise KoroneError.inaccessible_message()
        return msg

    @property
    def callback_data(self) -> CallbackData | str | None:
        return self.data.get("callback_data")

    async def answer_media(self, f: InputFile, caption: str | None = None, **kwargs: dict[str, Any]) -> Message | bool:
        if isinstance(self.event, InaccessibleMessage):
            raise KoroneError.inaccessible_message()
        if isinstance(self.event, CallbackQuery) and self.event.message:
            return await bot.edit_message_media(
                media=InputMediaPhoto(media=f, caption=caption),
                chat_id=self.event.message.chat.id,
                message_id=self.event.message.message_id,
                **cast("Any", kwargs),
            )
        if isinstance(self.event, Message):
            return await bot.send_photo(chat_id=self.event.chat.id, photo=f, caption=caption, **cast("Any", kwargs))
        msg = "answer_media: Wrong event type"
        raise ValueError(msg)

    async def answer(self, text: Element | str, **kwargs: object) -> Message | bool:
        return await reply_or_edit(self.event, text, **cast("Any", kwargs))
