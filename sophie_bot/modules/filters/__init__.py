from aiogram import Router

from sophie_bot.modules.filters.enforce_middleware import EnforceFiltersMiddleware
from sophie_bot.utils.i18n import lazy_gettext as l_

__module_name__ = l_("Filters")
__module_emoji__ = "🪄"

router = Router(name="filters")


async def __pre_setup__():
    router.message.outer_middleware(EnforceFiltersMiddleware())
