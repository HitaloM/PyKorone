from aiogram import Router
from stfu_tg import Doc

from korone.modules.metadata import ModuleManifest, ModulePackage

from .handlers.event import EventHandler
from .handlers.redis_clear import RedisClearHandler
from .handlers.stats import StatsHandler, get_system_stats

router = Router(name="op")

manifest = ModuleManifest(
    package=ModulePackage(
        name="Operator",
        icon="👑",
        summary="Operator-only administration commands",
        description=Doc("Maintenance tools for diagnostics, cache control, and event inspection."),
        public=False,
    ),
    router=router,
    handlers=(EventHandler, StatsHandler, RedisClearHandler),
    stats=get_system_stats,
)
