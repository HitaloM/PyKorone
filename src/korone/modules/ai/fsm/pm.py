from aiogram.fsm.state import State, StatesGroup
from stfu_tg import Template

from korone.constants import AI_EMOJI
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_


class AiPMFSM(StatesGroup):
    in_ai = State()


AI_PM_STOP_TEXT = l_("🛑 Exit AI mode")
AI_PM_RESET = l_("🔄 Reset AI context")
AI_GENERATED_TEXT = l_(lambda: Template(_("{ai_emoji} Korone AI"), ai_emoji=AI_EMOJI).to_html())
