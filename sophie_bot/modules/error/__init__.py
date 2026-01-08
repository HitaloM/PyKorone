from aiogram import Router

from sophie_bot.filters.user_status import IsOP
from sophie_bot.utils.i18n import lazy_gettext as l_
from .handlers.crash_handler import crash_handler
from .handlers.error import SophieErrorHandler
from ...filters.cmd import CMDFilter
from ...middlewares import try_localization_middleware

router = Router(name="error")

__module_name__ = l_("Error")
__module_emoji__ = "🚫"
__exclude_public__ = True


async def __pre_setup__():
    router.message.register(crash_handler, CMDFilter("op_crash"), IsOP(True))

    router.error.middleware(try_localization_middleware)
    router.error.register(SophieErrorHandler)
