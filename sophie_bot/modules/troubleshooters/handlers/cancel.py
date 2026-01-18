from typing import Any

from aiogram import flags
from aiogram.types import ReplyKeyboardRemove
from stfu_tg import Italic, Template

from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Cancel current state, use if Sophie is not responding on your message"))
class CancelState(SophieMessageHandler):
    async def handle(self) -> Any:
        current_state = await self.state.get_state()

        if current_state is None:
            await self.event.answer(
                _("The current state is already cleared, wiping its data anyway..."),
            )
            await self.state.clear()
            return

        await self.state.clear()
        current_state = await self.state.get_state()
        await self.event.answer(
            Template(_("Current state {state} is cleared."), state=Italic(current_state)).to_html(),
            reply_markup=ReplyKeyboardRemove(),
        )
