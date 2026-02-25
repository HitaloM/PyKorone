from aiogram import Router
from stfu_tg import Doc

from korone.filters.user_status import IsOP as IsOP
from korone.middlewares import try_localization_middleware

from .handlers.crash_handler import CrashHandler
from .handlers.error import KoroneErrorHandler

router = Router(name="error")

__module_name__ = "Error"
__module_emoji__ = "🚫"
__module_description__ = "Error handling and reporting"
__module_info__ = Doc(
    "Handles errors and exceptions that occur during bot operation.",
    "Provides error reporting and recovery mechanisms.",
)

__exclude_public__ = True

__handlers__ = (CrashHandler,)


def __pre_setup__() -> None:
    router.error.middleware(try_localization_middleware)
    router.error.register(KoroneErrorHandler)
