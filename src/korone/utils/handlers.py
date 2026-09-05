from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, TypeVar, cast

import sentry_sdk
from aiogram.handlers import BaseHandler, MessageHandlerCommandMixin
from aiogram.types import CallbackQuery, InlineQuery, InputMediaPhoto, Message
from structlog.contextvars import bind_contextvars

from korone.args.base import PARSED_ARGUMENTS_KEY
from korone.middlewares.context_data import as_korone_context
from korone.modules.utils_.message import get_message
from korone.modules.utils_.reply_or_edit import reply_message, reply_or_edit, reply_or_edit_rich
from korone.ui.rendering import caption_kwargs

if TYPE_CHECKING:
    from collections.abc import Generator

    from aiogram import Router
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.filters.callback_data import CallbackData
    from aiogram.types import InputFile, InputRichMessage

    from korone.args import ArgumentSchema
    from korone.middlewares.chat_context import ChatContext
    from korone.middlewares.context_data import KoroneContextData
    from korone.ui import MessageContent


# BaseHandler's Generic/ABC hierarchy requires legacy generic syntax at this boundary.
T = TypeVar("T")


class KoroneBaseHandler(BaseHandler[T], ABC):
    def __await__(self) -> Generator[Any, None, Any]:
        handler_name = self.__class__.__name__
        bind_contextvars(handler=handler_name)
        sentry_sdk.set_tag("korone.handler", handler_name)
        return self.handle().__await__()

    @property
    def context(self) -> KoroneContextData:
        return as_korone_context(self.data)

    @property
    def chat(self) -> ChatContext:
        return self.context["chat"]

    @property
    def current_locale(self) -> str:
        return self.data["i18n"].current_locale

    @classmethod
    @abstractmethod
    def register(cls, router: Router) -> None:
        pass


class KoroneMessageHandler[ArgumentsT = None](MessageHandlerCommandMixin, KoroneBaseHandler[Message]):
    arguments: ArgumentSchema[ArgumentsT] | None = None

    @classmethod
    @abstractmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        pass

    @classmethod
    def register(cls, router: Router) -> None:
        flags = {"args": cls.arguments} if cls.arguments else None

        router.message.register(cls, *cls.filters(), flags=flags)

    @property
    def args(self) -> ArgumentsT:
        if type(self).arguments is None:
            return cast("ArgumentsT", None)
        try:
            return cast("ArgumentsT", self.data[PARSED_ARGUMENTS_KEY])
        except KeyError as exc:
            msg = "Handler arguments were accessed before parsing"
            raise RuntimeError(msg) from exc

    async def answer(self, text: MessageContent, **kwargs: object) -> Message:
        return await reply_message(self.event, text, **kwargs)


class KoroneCallbackQueryHandler(KoroneBaseHandler[CallbackQuery], ABC):
    @classmethod
    @abstractmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        pass

    @classmethod
    def register(cls, router: Router) -> None:
        router.callback_query.register(cls, *cls.filters())

    @property
    def callback_data(self) -> CallbackData | str:
        return self.data["callback_data"]

    @property
    def message(self) -> Message:
        return get_message(self.event)

    async def check_for_message(self) -> None:
        get_message(self.event)

    async def edit_text(self, text: MessageContent, **kwargs: object) -> None:
        await reply_or_edit(self.event, text, **kwargs)

    async def edit_rich(self, rich_message: InputRichMessage, **kwargs: object) -> None:
        await reply_or_edit_rich(self.event, rich_message, **kwargs)


class KoroneInlineQueryHandler(KoroneBaseHandler[InlineQuery], ABC):
    @classmethod
    @abstractmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        pass

    @classmethod
    def register(cls, router: Router) -> None:
        router.inline_query.register(cls, *cls.filters())


class KoroneMessageCallbackQueryHandler(KoroneBaseHandler[Message | CallbackQuery], ABC):
    @property
    def message(self) -> Message:
        return get_message(self.event)

    @property
    def callback_data(self) -> CallbackData | str | None:
        return self.data.get("callback_data")

    async def answer_media(
        self, f: InputFile, caption: MessageContent | None = None, **kwargs: object
    ) -> Message | bool:
        caption_payload = caption_kwargs(caption) if caption is not None else {}
        if isinstance(self.event, CallbackQuery):
            message = self.message
            media = InputMediaPhoto(media=f, **caption_payload)
            if message.ephemeral_message_id is not None:
                return await message.edit_ephemeral_media(media=media, **cast("dict[str, Any]", kwargs))
            return await self.bot.edit_message_media(
                media=media, chat_id=message.chat.id, message_id=message.message_id, **cast("dict[str, Any]", kwargs)
            )
        if isinstance(self.event, Message):
            return await self.bot.send_photo(
                chat_id=self.event.chat.id, photo=f, **caption_payload, **cast("dict[str, Any]", kwargs)
            )
        msg = "answer_media: Wrong event type"
        raise ValueError(msg)

    async def answer(self, text: MessageContent, **kwargs: object) -> Message | bool:
        return await reply_or_edit(self.event, text, **kwargs)

    async def answer_rich(self, rich_message: InputRichMessage, **kwargs: object) -> Message | bool:
        return await reply_or_edit_rich(self.event, rich_message, **kwargs)
