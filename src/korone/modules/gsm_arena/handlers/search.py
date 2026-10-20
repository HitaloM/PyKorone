from dataclasses import dataclass
from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.enums import ChatAction
from aiogram.filters import Command

from korone.args import ArgumentSchema, TextArg
from korone.modules.gsm_arena.utils.device import get_device_presentation, reply_with_device
from korone.modules.gsm_arena.utils.errors import GSMArenaError
from korone.modules.gsm_arena.utils.failures import report_failure
from korone.modules.gsm_arena.utils.keyboard import create_pagination_layout
from korone.modules.gsm_arena.utils.scraper import search_phone
from korone.modules.gsm_arena.utils.session import create_search_session
from korone.ui import Bold, Code, column, template
from korone.utils.exception import KoroneError
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType

    from korone.modules.gsm_arena.utils.types import PhoneSearchResult


@dataclass(frozen=True, slots=True)
class DeviceSearchArguments:
    device: str


@flags.help(description=l_("Search GSMArena for device specifications."))
@flags.chat_action(action=ChatAction.TYPING, initial_sleep=0.7)
@flags.disableable(name="device")
class DeviceSearchHandler(KoroneMessageHandler[DeviceSearchArguments]):
    arguments = ArgumentSchema(DeviceSearchArguments, device=TextArg(l_("Device")))

    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return (Command("device", "specs", "d"),)

    async def _answer_device(self, url: str) -> None:
        try:
            presentation = await get_device_presentation(url)
        except GSMArenaError as exc:
            await self.answer(await report_failure(exc, operation="details"))
            return

        await reply_with_device(self.event, presentation)

    async def _handle_search_results(self, query: str, devices: list[PhoneSearchResult]) -> None:
        if not devices:
            await self.answer(_("No devices found."))
            return

        if len(devices) == 1:
            await self._answer_device(devices[0].url)
            return

        if not self.event.from_user:
            raise KoroneError.user_context_unavailable()

        session_token = await create_search_session(devices)
        keyboard = create_pagination_layout(devices, session_token, 1, self.event.from_user.id)
        text = column(
            template(_("Search results for: {query}"), query=Bold(query)),
            template(_("Found {count} devices. Select one from the list below."), count=Code(str(len(devices)))),
        )
        await self.answer(text, reply_markup=keyboard)

    async def handle(self) -> None:
        query = self.args.device

        try:
            devices = await search_phone(query)
        except GSMArenaError as exc:
            await self.answer(await report_failure(exc, operation="search"))
            return

        await self._handle_search_results(query, devices)
