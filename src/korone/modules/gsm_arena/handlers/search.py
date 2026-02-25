from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiogram import flags
from aiogram.enums import ChatAction
from ass_tg.types import TextArg
from stfu_tg import Bold, Code, Doc, Template

from korone.filters.cmd import CMDFilter
from korone.logger import get_logger
from korone.modules.gsm_arena.utils.device import get_device_text
from korone.modules.gsm_arena.utils.keyboard import create_pagination_layout
from korone.modules.gsm_arena.utils.scraper import search_phone
from korone.modules.gsm_arena.utils.session import create_search_session
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import Message
    from ass_tg.types.base_abc import ArgFabric

    from korone.modules.gsm_arena.utils.types import PhoneSearchResult

logger = get_logger(__name__)


@flags.help(description=l_("Search device specifications on GSMArena."))
@flags.chat_action(action=ChatAction.TYPING, initial_sleep=0.7)
@flags.disableable(name="device")
class DeviceSearchHandler(KoroneMessageHandler):
    @classmethod
    async def handler_args(cls, message: Message | None, data: dict[str, Any]) -> dict[str, ArgFabric]:
        return {"device": TextArg(l_("Device"))}

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter(("device", "specs", "d")),)

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

        if not self.event.from_user:
            msg = "User information is not available in the handler context."
            raise RuntimeError(msg)

        session_token = await create_search_session(devices)
        keyboard = create_pagination_layout(devices, session_token, 1, self.event.from_user.id)
        text = Doc(
            Template(_("Search results for: {query}"), query=Bold(query)),
            Template(_("Found {count} devices. Select one from the list below."), count=Code(str(len(devices)))),
        )
        await self.event.reply(str(text), reply_markup=keyboard)

    async def handle(self) -> None:
        query = (self.data.get("device") or "").strip()

        if not query:
            await self.event.reply(
                Template(
                    _("You should provide a device name to search. Example: {example}."),
                    example=Code("/device Galaxy S24"),
                ).to_html()
            )
            return

        devices = await search_phone(query)
        await self._handle_search_results(query, devices)
