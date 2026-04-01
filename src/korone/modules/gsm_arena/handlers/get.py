import re
from typing import TYPE_CHECKING, cast

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


def _is_message_not_modified(error: TelegramBadRequest) -> bool:
    return "message is not modified" in error.message.lower()


def _is_text_send_fallback_error(error: TelegramBadRequest) -> bool:
    lowered_message = error.message.lower()
    return "message is too long" in lowered_message or "can't parse entities" in lowered_message


def _to_plain_text(html_text: str) -> str:
    plain_text = re.sub(r"<[^>]+>", "", html_text)
    return plain_text.strip()


def _chunk_text(value: str, chunk_size: int) -> list[str]:
    return [value[i : i + chunk_size] for i in range(0, len(value), chunk_size)]


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
            await self.event.answer(_("Error fetching device details"), show_alert=True)
            return

        chunk_size = TELEGRAM_MESSAGE_LENGTH_LIMIT - 50
        for chunk in _chunk_text(plain_text, chunk_size):
            await message.reply(text=chunk, link_preview_options=link_preview_options)
