from aiogram import Router

from korone.middlewares import try_localization_middleware
from korone.utils.i18n import lazy_gettext as l_

from .handlers.crash_handler import CrashHandler
from .handlers.error import KoroneErrorHandler

router = Router(name="error")

__module_name__ = l_("Error")
__module_emoji__ = "🚫"
__exclude_public__ = True

__handlers__ = (CrashHandler,)


def __pre_setup__() -> None:
    router.error.middleware(try_localization_middleware)
    router.error.register(KoroneErrorHandler)
