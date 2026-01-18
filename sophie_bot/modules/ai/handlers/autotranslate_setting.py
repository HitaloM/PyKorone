from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType

from sophie_bot.db.models.ai.ai_autotranslate import AIAutotranslateModel
from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.utils_.status_handler import StatusBoolHandlerABC
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(alias_to_modules=["language"], description=l_("Controls AI Auto translator"))
class AIAutotrans(StatusBoolHandlerABC):
    header_text = l_("✨ AI Auto translate")
    change_command = "aiautotranslate"

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter(("aiautotranslate", "autotranslate")), UserRestricting(admin=True)

    async def get_status(self) -> bool:
        if not self.connection.db_model:
            return False

        db_model = await AIAutotranslateModel.get_state(self.connection.db_model.iid)
        return bool(db_model)

    async def set_status(self, new_status: bool):
        await AIAutotranslateModel.set_state(self.connection.db_model, new_status)
