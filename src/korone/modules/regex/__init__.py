from aiogram import Router
from stfu_tg import Doc

from korone.utils.i18n import LazyProxy
from korone.utils.i18n import lazy_gettext as l_

from .handlers.sed import SedHandler

router = Router(name="regex")

__module_name__ = l_("Regex")
__module_emoji__ = "🧪"
__module_description__ = l_("Apply regex substitutions to replied messages.")
__module_info__ = LazyProxy(
    lambda: Doc(
        l_("Use sed-like syntax to replace text in a replied message. Example: s/old/new/g; escape slashes as \\/.")
    )
)

__handlers__ = (SedHandler,)
