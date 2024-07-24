from aiogram import Router

from sophie_bot.utils.i18n import lazy_gettext as l_

from ...filters.cmd import CMDFilter
from .handlers.cancel import CancelState

router = Router(name="troubleshooters")

__module_name__ = l_("Troubleshooters")
__module_emoji__ = "🧰"


def __pre_setup__():
    router.message.register(CancelState, CMDFilter("cancel"))
