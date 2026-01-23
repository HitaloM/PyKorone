from aiogram import Router
from stfu_tg import Doc

from korone.utils.i18n import LazyProxy
from korone.utils.i18n import lazy_gettext as l_

from .export import export_disabled
from .handlers.disable import DisableHandler
from .handlers.disable_able import ListDisableable
from .handlers.disabled import ListDisabled
from .handlers.enable import EnableHandler
from .handlers.enable_all import DisableAllCbHandler, EnableAllHandler

router = Router(name="Disable")

__module_name__ = l_("Disabling")
__module_emoji__ = "🚫"
__module_description__ = l_("Disable some commonly used commands.")
__module_info__ = LazyProxy(
    lambda: Doc(
        l_(
            "Not everyone wants every feature that Korone offers. Some commands are best left unused; to avoid spam and abuse."
        )
    )
)

__export__ = export_disabled

__handlers__ = (ListDisableable, ListDisabled, DisableHandler, EnableHandler, EnableAllHandler, DisableAllCbHandler)
