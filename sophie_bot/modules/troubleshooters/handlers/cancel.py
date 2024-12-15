from typing import Any

from aiogram import flags
from aiogram.fsm.context import FSMContext
from aiogram.handlers import MessageHandler
from aiogram.types import ReplyKeyboardRemove
from stfu_tg import Italic, Template

from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Cancel current state, use if Sophie is not responding on your message"))
class CancelState(MessageHandler):
    async def handle(self) -> Any:
        state: FSMContext = self.data["state"]

        current_state = await state.get_state()
        if current_state is None:
            await self.event.answer(
                _("The current state is already cleared, wiping its data anyway..."),
            )
            await state.clear()
            return

        await state.clear()
        current_state = await state.get_state()
        await self.event.answer(
            Template(_("Current state {state} is cleared."), state=Italic(current_state)).to_html(),
            reply_markup=ReplyKeyboardRemove(),
        )
