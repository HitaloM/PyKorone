from aiogram import Router

from sophie_bot.modules.notes.utils.buttons_processor.legacy import BUTTONS
from sophie_bot.modules.purges.handlers.button import LegacyDelMsgButton
from sophie_bot.modules.purges.handlers.delete import DelMsgCmdHandler
from sophie_bot.modules.purges.handlers.purge import PurgeMessagesHandler
from sophie_bot.modules.purges.magic_handlers.filter import get_filter
from sophie_bot.modules.purges.magic_handlers.modern_filter import DelMsgModernModern
from sophie_bot.utils.i18n import lazy_gettext as l_

__module_name__ = l_("Purges")
__module_emoji__ = "🗑"

__filters__ = get_filter()
__modern_actions__ = (DelMsgModernModern,)

BUTTONS.update({"delmsg": "btn_deletemsg_cb"})

router = Router(name="purges")

__handlers__ = (
    DelMsgCmdHandler,
    PurgeMessagesHandler,
    LegacyDelMsgButton,
)
