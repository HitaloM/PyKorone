from aiogram import Router

from sophie_bot.filters.user_status import IsOP

from ...filters.cmd import CMDFilter
from ...middlewares import try_localization_middleware
from .handlers.crash_handler import crash_handler
from .handlers.error import SophieErrorHandler

router = Router(name="error")


def __pre_setup__():
    router.message.register(crash_handler, CMDFilter("test_crash"), IsOP(True))

    router.error.middleware(try_localization_middleware)
    router.error.register(SophieErrorHandler)
