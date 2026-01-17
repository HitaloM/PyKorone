from aiogram import Router

from sophie_bot.modules.antiflood.api import api_router
from sophie_bot.modules.antiflood.handlers.antiflood_setting import AntifloodSetting
from sophie_bot.modules.antiflood.middlewares.enforcer import AntifloodEnforcerMiddleware
from sophie_bot.utils.i18n import lazy_gettext as l_

__all__ = [
    "router",
    "api_router",
    "__module_name__",
    "__module_emoji__",
    "__module_description__",
    "__handlers__",
    "__pre_setup__",
]

router = Router(name="antiflood")

__module_name__ = l_("Antiflood")
__module_emoji__ = "📈"
__module_description__ = l_("Protect your chat from message flooding")

__handlers__ = (AntifloodSetting,)


async def __pre_setup__() -> None:
    """Register middleware and any manual handlers."""
    router.message.outer_middleware(AntifloodEnforcerMiddleware())
