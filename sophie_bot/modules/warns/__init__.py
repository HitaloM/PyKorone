from aiogram import Router
from stfu_tg import Doc

from sophie_bot.modules.warns.api import api_router
from sophie_bot.modules.warns.handlers.warn import WarnHandler
from sophie_bot.modules.warns.magic_handlers.modern_action import WarnModernAction
from sophie_bot.utils.i18n import LazyProxy
from sophie_bot.utils.i18n import lazy_gettext as l_

__all__ = ("api_router",)

__modern_actions__ = (WarnModernAction,)

router = Router(name="warns")

__module_name__ = l_("Warnings")
__module_emoji__ = "⚠️"
__module_info__ = LazyProxy(
    lambda: Doc(
        l_("Warns users in the chat to keep it safe."),
        l_("You can set a max warning limit and an action to take when the limit is reached."),
    )
)


__handlers__ = (WarnHandler,)
