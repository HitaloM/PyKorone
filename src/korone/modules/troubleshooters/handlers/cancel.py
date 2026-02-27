from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardRemove
from stfu_tg import Italic, Template

from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


@flags.help(description=l_("Cancel the current interaction state."))
class CancelState(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (Command("cancel"),)

    async def handle(self) -> None:
        current_state = await self.state.get_state()

        if current_state is None:
            await self.event.answer(_("The current state is already cleared, wiping its data anyway..."))
            await self.state.clear()
            return

        await self.state.clear()
        current_state = await self.state.get_state()
        await self.event.answer(
            Template(_("Current state {state} is cleared."), state=Italic(current_state)).to_html(),
            reply_markup=ReplyKeyboardRemove(),
        )
