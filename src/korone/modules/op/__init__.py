from aiogram import Router

from korone.utils.i18n import lazy_gettext as l_

from .handlers.event import EventHandler
from .handlers.sqlite_info import SQLiteInfoHandler
from .handlers.stats import StatsHandler, get_system_stats

router = Router(name="op")

__module_name__ = l_("Operator")
__module_emoji__ = "👑"
__exclude_public__ = True

__handlers__ = (EventHandler, StatsHandler, SQLiteInfoHandler)
__stats__ = get_system_stats
