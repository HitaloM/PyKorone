from html.parser import HTMLParser
from typing import TYPE_CHECKING, Final, cast

from aiogram import flags
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import LinkPreviewOptions

from korone.constants import TELEGRAM_MESSAGE_LENGTH_LIMIT
from korone.logger import get_logger
from korone.modules.gsm_arena.callbacks import GetDeviceCallback
from korone.modules.gsm_arena.utils.device import get_device_text
from korone.modules.gsm_arena.utils.errors import GSMArenaError
from korone.modules.gsm_arena.utils.session import get_search_session
from korone.utils.handlers import KoroneCallbackQueryHandler
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import Message

logger = get_logger(__name__)
MESSAGE_NOT_MODIFIED_ERROR: Final[str] = "message is not modified"
TELEGRAM_MESSAGE_SAFE_MARGIN: Final[int] = 50


def _is_message_not_modified(error: TelegramBadRequest) -> bool:
    return MESSAGE_NOT_MODIFIED_ERROR in error.message.lower()


def _is_text_send_fallback_error(error: TelegramBadRequest) -> bool:
    lowered_message = error.message.lower()
    return "message is too long" in lowered_message or "can't parse entities" in lowered_message


class _PlainTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._text_fragments: list[str] = []

    def handle_data(self, data: str) -> None:
        self._text_fragments.append(data)

    def get_text(self) -> str:
        return "".join(self._text_fragments).strip()


def _to_plain_text(html_text: str) -> str:
    parser = _PlainTextExtractor()
    try:
        parser.feed(html_text)
        parser.close()
    except ValueError as exc:
        logger.warning(
            "gsm_arena_html_plain_text_parser_failed",
            error_type=type(exc).__name__,
            original_text_length=len(html_text),
        )
        return ""
    return parser.get_text()


def _chunk_text(value: str, chunk_size: int) -> list[str]:
    if not value:
        return []

    words = value.split()
    chunks: list[str] = []
    current_chunk = ""

    for word in words:
        candidate = word if not current_chunk else f"{current_chunk} {word}"
        if len(candidate) <= chunk_size:
            current_chunk = candidate
            continue

        if current_chunk:
            chunks.append(current_chunk)
        if len(word) > chunk_size:
            chunks.extend(word[i : i + chunk_size] for i in range(0, len(word), chunk_size))
            current_chunk = ""
            continue
        current_chunk = word

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


@flags.help(exclude=True)
class DeviceGetCallbackHandler(KoroneCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (GetDeviceCallback.filter(),)

    async def handle(self) -> None:
        await self.check_for_message()

        callback_data = cast("GetDeviceCallback", self.callback_data)

        if self.event.from_user.id != callback_data.user_id:
            await self.event.answer(_("You are not allowed to use this button."), show_alert=True)
            return

        devices = await get_search_session(callback_data.token)
        if devices is None:
            await self.event.answer(_("Search session expired. Please run /device again."), show_alert=True)
            return

        if callback_data.index < 0 or callback_data.index >= len(devices):
            await self.event.answer(_("Invalid device selected."), show_alert=True)
            return

        await self.event.answer(_("Fetching device details..."))

        try:
            text = await get_device_text(devices[callback_data.index].url)
        except GSMArenaError as exc:
            await logger.awarning(
                "[GSM Arena] Device details callback failed",
                device_url=devices[callback_data.index].url,
                error_type=type(exc).__name__,
            )
            await self.event.answer(_("Error fetching device details"), show_alert=True)
            return

        if not text:
            await self.event.answer(_("Error fetching device details"), show_alert=True)
            return

        message = cast("Message", self.event.message)
        link_preview_options = LinkPreviewOptions(disable_web_page_preview=False, prefer_large_media=True)

        try:
            if message.chat.type == ChatType.PRIVATE:
                await message.reply(text=text, link_preview_options=link_preview_options)
            else:
                await self.edit_text(text=text, link_preview_options=link_preview_options)
            return
        except TelegramBadRequest as err:
            if _is_message_not_modified(err):
                return
            if not _is_text_send_fallback_error(err):
                raise

        plain_text = _to_plain_text(text)
        if not plain_text:
            await logger.awarning(
                "gsm_arena_empty_plain_text_fallback",
                device_url=devices[callback_data.index].url,
                original_text_length=len(text),
            )
            await self.event.answer(_("Error fetching device details"), show_alert=True)
            return

        chunk_size = TELEGRAM_MESSAGE_LENGTH_LIMIT - TELEGRAM_MESSAGE_SAFE_MARGIN
        for chunk in _chunk_text(plain_text, chunk_size):
            await message.reply(text=chunk, link_preview_options=link_preview_options)
