from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, NotRequired, TypedDict, TypeVar, Unpack, cast

from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.handlers import BaseHandler, BaseHandlerMixin
from aiogram.types import CallbackQuery, InaccessibleMessage, InputMediaPhoto, Message, TelegramObject
from aiogram.utils.i18n import I18n
from ass_tg.types.base_abc import ArgFabric

from korone import bot
from korone.db.models.chat import ChatModel, UserInGroupModel
from korone.middlewares.chat_context import ChatContext
from korone.modules.utils_.reply_or_edit import reply_or_edit
from korone.utils.exception import KoroneException
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from aiogram import Router
    from aiogram.client.default import Default
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import (
        InlineKeyboardMarkup,
        InputFile,
        LinkPreviewOptions,
        MessageEntity,
        ReplyMarkupUnion,
        ReplyParameters,
        SuggestedPostParameters,
    )
    from stfu_tg.doc import Element

T = TypeVar("T")

type HandlerResult = TelegramObject | bool | None
type JsonPrimitive = str | int | float | bool | None
type JsonDict = dict[str, JsonPrimitive]
type HandlerArgsMap = dict[str, ArgFabric]
type HandlerDataValue = (
    str
    | int
    | float
    | bool
    | TelegramObject
    | list[TelegramObject]
    | list[str]
    | list[int]
    | JsonDict
    | ChatContext
    | ChatModel
    | UserInGroupModel
    | FSMContext
    | I18n
    | CallbackData
    | ArgFabric
    | HandlerArgsMap
    | None
)
type HandlerData = dict[str, HandlerDataValue]


class EditTextKwargs(TypedDict, total=False):
    parse_mode: NotRequired[str | Default | None]
    entities: NotRequired[list[MessageEntity] | None]
    link_preview_options: NotRequired[LinkPreviewOptions | Default | None]
    reply_markup: NotRequired[InlineKeyboardMarkup | None]
    disable_web_page_preview: NotRequired[bool | Default | None]


class EditMessageMediaKwargs(TypedDict, total=False):
    business_connection_id: NotRequired[str | None]
    reply_markup: NotRequired[InlineKeyboardMarkup | None]
    request_timeout: NotRequired[int | None]


class SendPhotoKwargs(TypedDict, total=False):
    business_connection_id: NotRequired[str | None]
    message_thread_id: NotRequired[int | None]
    direct_messages_topic_id: NotRequired[int | None]
    parse_mode: NotRequired[str | Default | None]
    caption_entities: NotRequired[list[MessageEntity] | None]
    show_caption_above_media: NotRequired[bool | Default | None]
    has_spoiler: NotRequired[bool | None]
    disable_notification: NotRequired[bool | None]
    protect_content: NotRequired[bool | Default | None]
    allow_paid_broadcast: NotRequired[bool | None]
    message_effect_id: NotRequired[str | None]
    suggested_post_parameters: NotRequired[SuggestedPostParameters | None]
    reply_parameters: NotRequired[ReplyParameters | None]
    reply_markup: NotRequired[ReplyMarkupUnion | None]
    allow_sending_without_reply: NotRequired[bool | None]
    reply_to_message_id: NotRequired[int | None]
    request_timeout: NotRequired[int | None]


class AnswerMediaKwargs(EditMessageMediaKwargs, SendPhotoKwargs, total=False):
    pass


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
    async def handler_args(cls, message: Message | None, data: HandlerData) -> dict[str, ArgFabric]:
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
            raise KoroneException("Not a user clicked a button")

        if not self.event.message or isinstance(self.event.message, InaccessibleMessage):
            raise KoroneException(_("The message is inaccessible. Please write the command again"))

    async def edit_text(self, text: Element | str, **kwargs: Unpack[EditTextKwargs]) -> None:
        await self.check_for_message()
        message = cast("Message", self.event.message)
        edit_kwargs = cast("EditTextKwargs", kwargs)
        await message.edit_text(str(text), **edit_kwargs)


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
    def callback_data(self) -> CallbackData | str | None:
        return self.data.get("callback_data")

    async def answer_media(
        self, f: InputFile, caption: str | None = None, **kwargs: Unpack[AnswerMediaKwargs]
    ) -> Message | bool:
        if isinstance(self.event, InaccessibleMessage):
            raise KoroneException(_("The message is inaccessible. Please write the command again"))
        elif isinstance(self.event, CallbackQuery) and self.event.message:
            edit_kwargs = cast("EditMessageMediaKwargs", kwargs)
            return await bot.edit_message_media(
                media=InputMediaPhoto(media=f, caption=caption),
                chat_id=self.event.message.chat.id,
                message_id=self.event.message.message_id,
                **edit_kwargs,
            )
        elif isinstance(self.event, Message):
            send_kwargs = cast("SendPhotoKwargs", kwargs)
            return await bot.send_photo(chat_id=self.event.chat.id, photo=f, caption=caption, **send_kwargs)
        else:
            raise ValueError("answer_media: Wrong event type")

    async def answer(self, text: Element | str, **kwargs: Unpack[EditTextKwargs]) -> Message | bool:
        return await reply_or_edit(self.event, text, **kwargs)
