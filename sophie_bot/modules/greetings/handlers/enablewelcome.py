from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType

from sophie_bot.db.models.greetings import GreetingsModel
from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.utils_.status_handler import StatusBoolHandlerABC
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Shows / changes the state of sending greetings"))
class EnableWelcomeHandlerABC(StatusBoolHandlerABC):
    header_text = l_("Welcome messages")
    change_command = "enablewelcome"

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter("enablewelcome"), UserRestricting(admin=True)

    async def get_status(self) -> bool:
        chat_id = self.connection.tid
        db_model = await GreetingsModel.get_by_chat_id(chat_id)
        return (not db_model.welcome_disabled) if db_model else False

    async def set_status(self, new_status: bool):
        chat_id = self.connection.tid
        await GreetingsModel.change_state_welcome(chat_id, new_status)
