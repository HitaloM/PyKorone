from aiogram import Router
from stfu_tg import Doc

from korone.modules.metadata import ModuleExport, ModuleManifest, ModulePackage
from korone.utils.i18n import LazyProxy
from korone.utils.i18n import lazy_gettext as l_

from .export import export_disabled
from .handlers.disable import DisableHandler
from .handlers.disable_able import ListDisableable
from .handlers.disabled import ListDisabled
from .handlers.enable import EnableHandler
from .handlers.enable_all import DisableAllCbHandler, EnableAllHandler

router = Router(name="Disable")

manifest = ModuleManifest(
    package=ModulePackage(
        name=l_("Disabling"),
        icon="🚫",
        summary=l_("Command toggles for group chats"),
        description=LazyProxy(
            lambda: Doc(
                l_("Let admins disable specific commands per chat."),
                l_("Useful for keeping only the features your group actually needs."),
            )
        ),
    ),
    router=router,
    handlers=(ListDisableable, ListDisabled, DisableHandler, EnableHandler, EnableAllHandler, DisableAllCbHandler),
    export=ModuleExport(export_disabled),
)
