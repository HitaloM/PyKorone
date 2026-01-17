import importlib

from aiogram import Router

from sophie_bot.utils.i18n import lazy_gettext as l_

from .export import privacy_export
from .stats import users_stats

__stats__ = users_stats

router = Router(name="users")


__module_name__ = l_("Users")
__module_emoji__ = "🫂"


__export__ = privacy_export


async def __pre_setup__():
    router.include_router(importlib.import_module(".handlers.id", __package__).router)
    router.include_router(importlib.import_module(".handlers.info", __package__).router)
    router.include_router(importlib.import_module(".handlers.adminlist", __package__).router)
