from aiogram import Router

from .api import api_router as api_router
from sophie_bot.modules.disabling.export import export_disabled
from sophie_bot.modules.disabling.handlers.disable import DisableHandler
from sophie_bot.modules.disabling.handlers.disable_able import ListDisableable
from sophie_bot.modules.disabling.handlers.disabled import ListDisabled
from sophie_bot.modules.disabling.handlers.enable import EnableHandler
from sophie_bot.modules.disabling.handlers.enable_all import (
    DisableAllCbHandler,
    EnableAllHandler,
)
from sophie_bot.utils.i18n import lazy_gettext as l_

__all__ = ("api_router",)

router = Router(name="Disable")


__module_name__ = l_("Disabling")
__module_emoji__ = "🚫"

__export__ = export_disabled


async def __pre_setup__():
    router.message.register(ListDisableable, *ListDisableable.filters())
    router.message.register(ListDisabled, *ListDisabled.filters())
    router.message.register(DisableHandler, *DisableHandler.filters())
    router.message.register(EnableHandler, *EnableHandler.filters())
    router.message.register(EnableAllHandler, *EnableAllHandler.filters())

    router.callback_query.register(DisableAllCbHandler, *DisableAllCbHandler.filters())
