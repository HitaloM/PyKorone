from typing import Any

from aiogram import flags
from ass_tg.types import IntArg

from sophie_bot.db.models import BetaModeModel, GlobalSettings
from sophie_bot.utils.handlers import SophieMessageHandler


@flags.args(
    percentage=IntArg(),
)
class SetBetaPercentage(SophieMessageHandler):
    async def handle(self) -> Any:
        percentage: int = self.data["percentage"]

        if percentage < 0 or percentage > 100:
            return await self.event.reply("Please enter a number between 0 and 100.")

        model = await GlobalSettings.set_by_key("beta_percentage", percentage)
        return await self.event.reply(f"The beta percentage has been set to {model.value}% for all new chats.")


class ResetBetaChats(SophieMessageHandler):
    async def handle(self) -> Any:
        await BetaModeModel.all_chats_reset_current_mode()
        return await self.event.reply("The chosen beta mode has been reset for all chats.")
