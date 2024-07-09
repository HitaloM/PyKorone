from typing import Any

from aiogram.fsm.context import FSMContext
from aiogram.handlers import MessageHandler
from aiogram.types import ReplyKeyboardRemove

from sophie_bot.utils.i18n import gettext as _


class CancelState(MessageHandler):
    async def handle(self) -> Any:
        state: FSMContext = self.data["state"]

        current_state = await state.get_state()
        if current_state is None:
            await self.event.answer(
                _("The current state is already cleared, nothing to do here."),
            )
            return

        await state.clear()
        await self.event.answer(
            _("Current state is cleared."),
            reply_markup=ReplyKeyboardRemove(),
        )
