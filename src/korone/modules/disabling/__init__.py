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
__module_description__ = l_("Command toggles for group chats")
__module_info__ = LazyProxy(
    lambda: Doc(
        l_("Let admins disable specific commands per chat."),
        l_("Useful for keeping only the features your group actually needs."),
    )
)

__export__ = export_disabled

__handlers__ = (ListDisableable, ListDisabled, DisableHandler, EnableHandler, EnableAllHandler, DisableAllCbHandler)
