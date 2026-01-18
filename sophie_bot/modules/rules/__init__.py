from aiogram import Router

from .api import api_router as api_router
from sophie_bot.modules.notes.utils.buttons_processor.legacy import BUTTONS
from sophie_bot.modules.rules.handlers.get import GetRulesHandler
from sophie_bot.modules.rules.handlers.legacy_button import LegacyRulesButton
from sophie_bot.modules.rules.handlers.reset import ResetRulesHandler
from sophie_bot.modules.rules.handlers.set import SetRulesHandler
from sophie_bot.modules.rules.magic_handlers.filter import get_filter
from sophie_bot.modules.rules.magic_handlers.modern_filter import SendRulesAction
from sophie_bot.utils.i18n import lazy_gettext as l_

__module_name__ = l_("Rules")
__module_emoji__ = "🪧"

__filters__ = get_filter()
__modern_actions__ = (SendRulesAction,)

router = Router(name="rules")

BUTTONS.update({"rules": "btn_rules"})


__handlers__ = (
    SetRulesHandler,
    GetRulesHandler,
    ResetRulesHandler,
    LegacyRulesButton,
)
