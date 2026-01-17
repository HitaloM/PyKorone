import importlib

from aiogram import Router

from sophie_bot.utils.i18n import lazy_gettext as l_
from .handlers.adminlist import AdminListHandler
from .handlers.id import ShowIDHandler
from .handlers.info import UserInfoHandler

from .stats import users_stats

__stats__ = users_stats

router = Router(name="users")


__module_name__ = l_("Users")
__module_emoji__ = "🫂"


__handlers__ = (
    ShowIDHandler,
    AdminListHandler,
    UserInfoHandler,
)
