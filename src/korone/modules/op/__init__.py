from aiogram import Router
from stfu_tg import Doc

from .handlers.event import EventHandler
from .handlers.redis_clear import RedisClearHandler
from .handlers.stats import StatsHandler, get_system_stats

router = Router(name="op")

__module_name__ = "Operator"
__module_emoji__ = "👑"
__module_description__ = "Operator-only administration commands"
__module_info__ = Doc("Maintenance tools for diagnostics, cache control, and event inspection.")


__exclude_public__ = True

__handlers__ = (EventHandler, StatsHandler, RedisClearHandler)
__stats__ = get_system_stats
