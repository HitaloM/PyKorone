from aiogram import Router

from sophie_bot.modules.promotes.handlers.demote import DemoteUserHandler
from sophie_bot.modules.promotes.handlers.promote import PromoteUserHandler
from sophie_bot.utils.i18n import lazy_gettext as l_

__module_name__ = l_("Promotes")
__module_emoji__ = "⭐️"

router = Router(name="promotes")


__handlers__ = (
    PromoteUserHandler,
    DemoteUserHandler,
)
