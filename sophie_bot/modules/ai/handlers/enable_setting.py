from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType

from sophie_bot.constants import AI_EMOJI
from sophie_bot.db.models.ai.ai_enabled import AIEnabledModel
from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.utils_.status_handler import StatusBoolHandlerABC
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Controls AI features"))
class EnableAI(StatusBoolHandlerABC):
    header_text = l_(lambda: _("{ai_emoji} AI Features").format(ai_emoji=AI_EMOJI))
    change_command = "aienable"

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter(("enableai", "aienable")), UserRestricting(admin=True)

    async def get_status(self) -> bool:
        if not self.connection.db_model:
            return False

        chat_iid = self.connection.db_model.iid
        db_model = await AIEnabledModel.get_state(chat_iid)
        return bool(db_model)

    async def set_status(self, new_status: bool):
        await AIEnabledModel.set_state(self.connection.db_model, new_status)
