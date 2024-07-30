from aiogram import Router

from sophie_bot.utils.i18n import lazy_gettext as l_
from .handlers.id import ShowIDs
from .stats import users_stats

__stats__ = users_stats

from ...filters.cmd import CMDFilter

router = Router(name="notes")


__module_name__ = l_("Users")
__module_emoji__ = "🫂"


def __pre_setup__():
    router.message.register(ShowIDs, CMDFilter("id"))
