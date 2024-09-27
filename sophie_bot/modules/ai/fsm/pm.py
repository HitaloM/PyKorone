from aiogram.fsm.state import State, StatesGroup

from sophie_bot.utils.i18n import lazy_gettext as l_


class AiPMFSM(StatesGroup):
    in_ai = State()


AI_PM_STOP_TEXT = l_("🛑 Exit AI mode")

AI_GENERATED_TEXT = l_("✨ Beta AI")
