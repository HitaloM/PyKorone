from aiogram import Router
from stfu_tg import Doc

from korone.utils.i18n import LazyProxy
from korone.utils.i18n import lazy_gettext as l_

from .handlers.event import EventHandler
from .handlers.redis_clear import RedisClearHandler
from .handlers.stats import StatsHandler, get_system_stats

router = Router(name="op")

__module_name__ = l_("Operator")
__module_emoji__ = "👑"
__module_description__ = l_("Operator-only commands and tools")
__module_info__ = LazyProxy(
    lambda: Doc(
        l_("Provides operator-only commands and tools for bot administration."),
        l_("Includes system stats, job management, and other administrative functions."),
    )
)


__exclude_public__ = True

__handlers__ = (EventHandler, StatsHandler, RedisClearHandler)
__stats__ = get_system_stats
