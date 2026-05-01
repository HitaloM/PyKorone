from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, Final, Protocol, cast, override

from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ForceReply, InputMediaPhoto
from aiogram.utils.deep_linking import create_start_link
from aiogram.utils.keyboard import InlineKeyboardBuilder

from korone.db.repositories.lastfm import LastFMRepository
from korone.logger import get_logger
from korone.modules.lastfm.utils import LastFMError, format_lastfm_error
from korone.utils.handlers import KoroneCallbackQueryHandler, KoroneMessageHandler
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from aiogram import Bot
    from aiogram.fsm.context import FSMContext
    from aiogram.types import InlineKeyboardMarkup, Message

LASTFM_FALLBACK_IMAGE_URL = "https://lastfm.freetls.fastly.net/i/u/300x300/2a96cbd8b46e442fc41c2b86b821562f.png"
LASTFM_SET_START_PAYLOAD: Final[str] = "lastfm_set"

logger = get_logger(__name__)


class LastFMResponsePayload(Protocol):
    @property
    def text(self) -> str: ...

    @property
    def image_url(self) -> str | None: ...


@dataclass(slots=True, frozen=True)
class LastFMCallbackContext:
    username: str
    owner_id: int


class LastFMSetState(StatesGroup):
    waiting_username = State()


class LastFMHandlerSupport:
    _BAD_MEDIA_URL_ERROR_TOKENS: ClassVar[tuple[str, ...]] = (
        "wrong type of the web page content",
        "failed to get http url content",
    )

    @staticmethod
    async def build_username_setup_markup(bot: Bot) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text=_("Open private chat"), url=await create_start_link(bot, LASTFM_SET_START_PAYLOAD))
        return builder.as_markup()

    @staticmethod
    async def prompt_for_username(message: Message, state: FSMContext) -> None:
        await message.reply(_("Reply with your Last.fm username."), reply_markup=ForceReply(selective=True))
        await state.set_state(LastFMSetState.waiting_username)

    @classmethod
    async def reply_missing_username(cls, message: Message, *, bot: Bot, state: FSMContext) -> None:
        if message.chat.type == ChatType.PRIVATE:
            await cls.prompt_for_username(message, state)
            return

        await message.reply(cls.missing_username_text(), reply_markup=await cls.build_username_setup_markup(bot))

    @staticmethod
    def can_use_buttons(*, callback_owner_id: int, user_id: int) -> bool:
        return callback_owner_id in {0, user_id}

    @staticmethod
    async def resolve_username_for_user(user_id: int | None) -> str | None:
        if not user_id:
            return None

        return await LastFMRepository.get_username(user_id)

    @classmethod
    async def resolve_username_from_message(cls, message: Message) -> str | None:
        if not message.from_user:
            return None

        return await cls.resolve_username_for_user(message.from_user.id)

    @staticmethod
    def missing_username_text() -> str:
        return _("You need to set your Last.fm username first.")

    @staticmethod
    def resolve_image_url(image_url: str | None) -> str:
        return image_url or LASTFM_FALLBACK_IMAGE_URL

    @classmethod
    def _resolve_image_url_candidates(cls, image_url: str | None) -> tuple[str, ...]:
        primary_url = cls.resolve_image_url(image_url)
        if primary_url == LASTFM_FALLBACK_IMAGE_URL:
            return (LASTFM_FALLBACK_IMAGE_URL,)

        return (primary_url, LASTFM_FALLBACK_IMAGE_URL)

    @staticmethod
    def _normalize_telegram_error_message(exc: TelegramBadRequest) -> str:
        return exc.message.casefold()

    @classmethod
    def _is_bad_media_url_error(cls, exc: TelegramBadRequest) -> bool:
        normalized_message = cls._normalize_telegram_error_message(exc)
        return any(token in normalized_message for token in cls._BAD_MEDIA_URL_ERROR_TOKENS)

    @classmethod
    async def send_response(
        cls, message: Message, *, text: str, image_url: str | None, reply_markup: InlineKeyboardMarkup | None = None
    ) -> Message:
        for candidate_url in cls._resolve_image_url_candidates(image_url):
            try:
                return await message.reply_photo(photo=candidate_url, caption=text, reply_markup=reply_markup)
            except TelegramBadRequest as exc:
                if not cls._is_bad_media_url_error(exc):
                    raise
                await logger.awarning(
                    "[LastFM] Telegram rejected album art URL while sending response",
                    image_url=candidate_url,
                    chat_id=message.chat.id,
                    source_message_id=message.message_id,
                    error=exc.message,
                )

        return await message.reply(text, reply_markup=reply_markup)

    @classmethod
    async def edit_response(
        cls, message: Message, *, text: str, image_url: str | None, reply_markup: InlineKeyboardMarkup | None = None
    ) -> None:
        if not message.photo:
            await message.edit_text(text, reply_markup=reply_markup)
            return

        for candidate_url in cls._resolve_image_url_candidates(image_url):
            try:
                await message.edit_media(
                    media=InputMediaPhoto(media=candidate_url, caption=text), reply_markup=reply_markup
                )
            except TelegramBadRequest as exc:
                if not cls._is_bad_media_url_error(exc):
                    raise
                await logger.awarning(
                    "[LastFM] Telegram rejected album art URL while editing response",
                    image_url=candidate_url,
                    chat_id=message.chat.id,
                    target_message_id=message.message_id,
                    error=exc.message,
                )
            else:
                return

        await message.edit_caption(caption=text, reply_markup=reply_markup)


class BaseLastFMMessageHandler[P: LastFMResponsePayload](KoroneMessageHandler, LastFMHandlerSupport):
    async def resolve_username(self) -> str | None:
        return await type(self).resolve_username_from_message(self.event)

    @classmethod
    @abstractmethod
    async def build_payload_for_username(cls, *, username: str) -> P | None:
        pass

    @classmethod
    @abstractmethod
    def empty_state_text(cls) -> str:
        pass

    @classmethod
    def build_reply_markup_for_owner(cls, *, username: str, owner_id: int, payload: P) -> InlineKeyboardMarkup | None:
        return None

    @override
    async def handle(self) -> None:
        username = await self.resolve_username()
        if not username:
            await type(self).reply_missing_username(self.event, bot=self.bot, state=self.state)
            return

        try:
            payload = await type(self).build_payload_for_username(username=username)
        except LastFMError as exc:
            await self.event.reply(format_lastfm_error(exc))
            return

        if payload is None:
            await self.event.reply(type(self).empty_state_text())
            return

        owner_id = self.event.from_user.id if self.event.from_user else 0
        reply_markup = type(self).build_reply_markup_for_owner(username=username, owner_id=owner_id, payload=payload)
        await type(self).send_response(
            self.event, text=payload.text, image_url=payload.image_url, reply_markup=reply_markup
        )


class BaseLastFMCallbackHandler[C: LastFMCallbackContext, P: LastFMResponsePayload](
    KoroneCallbackQueryHandler, LastFMHandlerSupport
):
    @abstractmethod
    async def resolve_context(self) -> C | None:
        pass

    @classmethod
    @abstractmethod
    async def build_payload_for_username(cls, *, username: str) -> P | None:
        pass

    @classmethod
    async def build_payload(cls, *, context: C) -> P | None:
        return await cls.build_payload_for_username(username=context.username)

    @classmethod
    @abstractmethod
    def empty_state_text(cls) -> str:
        pass

    @classmethod
    def build_reply_markup_for_owner(cls, *, username: str, owner_id: int, payload: P) -> InlineKeyboardMarkup | None:
        return None

    async def handle_not_modified(self) -> None:
        await self._answer_callback_safely(_("No updates from your profile."))

    async def render_response(self, message: Message, *, context: C, payload: P) -> None:
        reply_markup = type(self).build_reply_markup_for_owner(
            username=context.username, owner_id=context.owner_id, payload=payload
        )
        await type(self).edit_response(
            message, text=payload.text, image_url=payload.image_url, reply_markup=reply_markup
        )

    @staticmethod
    def _is_message_not_modified(exc: TelegramBadRequest) -> bool:
        return "message is not modified" in exc.message.lower()

    @staticmethod
    def _is_callback_query_expired(exc: TelegramBadRequest) -> bool:
        message = exc.message.lower()
        return "query is too old" in message or "query id is invalid" in message

    async def _answer_callback_safely(self, text: str | None = None, *, show_alert: bool = False) -> None:
        try:
            await self.event.answer(text=text, show_alert=show_alert)
        except TelegramBadRequest as exc:
            if not self._is_callback_query_expired(exc):
                raise
            await logger.adebug(
                "LastFM callback query expired while answering", callback_query_id=self.event.id, error=exc.message
            )

    @override
    async def handle(self) -> None:
        await self.check_for_message()

        context = await self.resolve_context()
        if context is None:
            await self._answer_callback_safely()
            return

        if not self.can_use_buttons(callback_owner_id=context.owner_id, user_id=self.event.from_user.id):
            await self._answer_callback_safely(_("You are not allowed to use this button."), show_alert=True)
            return

        message = cast("Message", self.event.message)
        await self._answer_callback_safely()
        try:
            payload = await type(self).build_payload(context=context)
            if payload is None:
                await message.edit_text(type(self).empty_state_text())
            else:
                await self.render_response(message, context=context, payload=payload)
        except LastFMError as exc:
            await self._answer_callback_safely(format_lastfm_error(exc), show_alert=True)
        except TelegramBadRequest as exc:
            if self._is_message_not_modified(exc):
                await self.handle_not_modified()
                return
            raise
