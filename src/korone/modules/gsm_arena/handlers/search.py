from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.enums import ChatAction
from ass_tg.types import TextArg

from korone.filters.cmd import CMDFilter
from korone.logging import get_logger
from korone.modules.gsm_arena.utils.device import get_device_text
from korone.modules.gsm_arena.utils.keyboard import create_pagination_layout
from korone.modules.gsm_arena.utils.scraper import search_phone
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import Message
    from ass_tg.types.base_abc import ArgFabric

    from korone.modules.gsm_arena.utils.types import PhoneSearchResult
    from korone.utils.handlers import HandlerData

logger = get_logger(__name__)


@flags.help(description=l_("Search device specifications on GSMArena."))
@flags.disableable(name="device")
class DeviceSearchHandler(KoroneMessageHandler):
    @classmethod
    async def handler_args(cls, message: Message | None, data: HandlerData) -> dict[str, ArgFabric]:
        return {"device": TextArg(l_("Device"))}

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter(("device", "specs", "d")),)

    async def handle(self) -> None:
        query = (self.data.get("device") or "").strip()

        if not query:
            await self.event.reply(
                _("You should provide a device name to search. Example: <code>/device Galaxy S24</code>.")
            )
            return

        try:
            await self._send_typing_indicator()

            devices = await search_phone(query)
            await self._handle_search_results(query, devices)
        except Exception as exc:  # noqa: BLE001
            await logger.aerror("[GSM Arena] Error in device command", error=str(exc))
            await self.event.reply(_("An error occurred while searching. Please try again later."))

    async def _send_typing_indicator(self) -> None:
        if bot := self.event.bot:
            await bot.send_chat_action(chat_id=self.event.chat.id, action=ChatAction.TYPING)

    async def _handle_search_results(self, query: str, devices: list[PhoneSearchResult]) -> None:
        if not devices:
            await self.event.reply(_("No devices found."))
            return

        if len(devices) == 1:
            text = await get_device_text(devices[0].url)
            if text:
                await self.event.reply(text=text)
            else:
                await self.event.reply(_("Error fetching device details. Please try again later."))
            return

        keyboard = create_pagination_layout(devices, query, 1)
        await self.event.reply(_("Search results for: <b>{query}</b>").format(query=query), reply_markup=keyboard)
