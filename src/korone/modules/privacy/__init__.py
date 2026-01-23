from types import ModuleType

from aiogram import Router

from korone.modules import LOADED_MODULES
from korone.utils.i18n import LazyProxy as LazyProxy
from korone.utils.i18n import lazy_gettext as l_

from .callbacks import PrivacyMenuCallback as PrivacyMenuCallback
from .handlers.export import EXPORTABLE_MODULES, TriggerExport
from .handlers.privacy import PrivacyMenu

router = Router(name="info")

__module_name__ = l_("Privacy")
__module_emoji__ = "🕵️‍♂️️"
__module_description__ = l_("Data protection")
__module_info__ = l_("Manage your privacy settings and data protection options.")

__handlers__ = (PrivacyMenu, TriggerExport)


async def __post_setup__(modules: dict[str, ModuleType]):
    extra_modules = LOADED_MODULES.values() if isinstance(LOADED_MODULES, dict) else LOADED_MODULES
    for module in (*modules.values(), *extra_modules):
        if hasattr(module, "__export__"):
            EXPORTABLE_MODULES.append(module)
