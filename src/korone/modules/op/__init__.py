from aiogram import Router
from stfu_tg import Doc

from .handlers.event import EventHandler
from .handlers.redis_clear import RedisClearHandler
from .handlers.stats import StatsHandler, get_system_stats

router = Router(name="op")

__module_name__ = "Operator"
__module_emoji__ = "👑"
__module_description__ = "Operator-only commands and tools"
__module_info__ = Doc(
    "Provides operator-only commands and tools for bot administration.",
    "Includes system stats, job management, and other administrative functions.",
)


__exclude_public__ = True

__handlers__ = (EventHandler, StatsHandler, RedisClearHandler)
__stats__ = get_system_stats
