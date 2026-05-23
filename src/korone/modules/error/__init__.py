from aiogram import Router
from stfu_tg import Doc

from korone.filters.user_status import IsOP as IsOP
from korone.middlewares import try_localization_middleware
from korone.modules.metadata import ModuleManifest, ModulePackage, ModuleScripts

from .handlers.crash_handler import CrashHandler
from .handlers.error import KoroneErrorHandler

router = Router(name="error")


def pre_setup() -> None:
    router.error.middleware(try_localization_middleware)
    router.error.register(KoroneErrorHandler)


manifest = ModuleManifest(
    package=ModulePackage(
        name="Error",
        icon="🚫",
        summary="Error handling and diagnostics",
        description=Doc(
            "Internal handlers for runtime exceptions and recovery.",
            "Includes an operator-only crash command for testing.",
        ),
        public=False,
    ),
    router=router,
    handlers=(CrashHandler,),
    scripts=ModuleScripts(pre_setup=pre_setup),
)
