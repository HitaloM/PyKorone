from typing import TYPE_CHECKING, cast

from aiogram import flags
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import LinkPreviewOptions

from korone.logger import get_logger
from korone.modules.gsm_arena.callbacks import GetDeviceCallback
from korone.modules.gsm_arena.utils.device import get_device_text
from korone.modules.gsm_arena.utils.session import get_search_session
from korone.utils.handlers import KoroneCallbackQueryHandler
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import Message

logger = get_logger(__name__)


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

        text = await get_device_text(devices[callback_data.index].url)
        if not text:
            await self.event.answer(_("Error fetching device details"), show_alert=True)
            return

        message = cast("Message", self.event.message)
        if message.chat.type == ChatType.PRIVATE:
            await message.reply(
                text=text,
                link_preview_options=LinkPreviewOptions(disable_web_page_preview=False, prefer_large_media=True),
            )
        else:
            try:
                await message.edit_text(
                    text=text,
                    link_preview_options=LinkPreviewOptions(disable_web_page_preview=False, prefer_large_media=True),
                )
            except TelegramBadRequest as err:
                if "message is not modified" not in err.message:
                    raise
