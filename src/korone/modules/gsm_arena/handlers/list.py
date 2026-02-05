from typing import TYPE_CHECKING, cast

from aiogram import flags
from aiogram.exceptions import TelegramBadRequest

from korone.logging import get_logger
from korone.modules.gsm_arena.callbacks import DevicePageCallback
from korone.modules.gsm_arena.utils.keyboard import create_pagination_layout
from korone.modules.gsm_arena.utils.scraper import search_phone
from korone.utils.handlers import KoroneCallbackQueryHandler
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import Message

logger = get_logger(__name__)


@flags.help(exclude=True)
class DeviceListCallbackHandler(KoroneCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (DevicePageCallback.filter(),)

    async def handle(self) -> None:
        await self.check_for_message()

        callback_data = cast("DevicePageCallback", self.callback_data)
        devices = await search_phone(callback_data.device)
        if not devices:
            await self.event.answer(_("No devices found"), show_alert=True)
            return

        keyboard = create_pagination_layout(devices, callback_data.device, callback_data.page)
        message = cast("Message", self.event.message)

        try:
            await message.edit_reply_markup(reply_markup=keyboard)
        except TelegramBadRequest as err:
            if "message is not modified" not in err.message:
                raise

        await self.event.answer()
