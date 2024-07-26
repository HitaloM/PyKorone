from aiogram import Router

from sophie_bot.utils.i18n import lazy_gettext as l_

from ...filters.admin_rights import UserRestricting
from ...filters.cmd import CMDFilter
from .handlers.admincache import ResetAdminCache
from .handlers.cancel import CancelState

router = Router(name="troubleshooters")

__module_name__ = l_("Troubleshooters")
__module_emoji__ = "🧰"
__module_info__ = l_("Small commands for fixing problems")


def __pre_setup__():
    router.message.register(CancelState, CMDFilter("cancel"))
    router.message.register(ResetAdminCache, CMDFilter("admincache"), UserRestricting(admin=True))
