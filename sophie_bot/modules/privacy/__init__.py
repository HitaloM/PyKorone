from types import ModuleType

from aiogram import Router

from sophie_bot.utils.i18n import lazy_gettext as l_

from ...filters.chat_status import ChatTypeFilter
from ...filters.cmd import CMDFilter
from sophie_bot.modules import LOADED_MODULES
from .callbacks import PrivacyMenuCallback
from .handlers.export import EXPORTABLE_MODULES, TriggerExport
from .handlers.privacy import PrivacyMenu

router = Router(name="info")


__module_name__ = l_("Privacy")
__module_emoji__ = "🕵️‍♂️️"
__module_description__ = l_("Data protection")


async def __pre_setup__():
    router.message.register(PrivacyMenu, CMDFilter("privacy"), ChatTypeFilter("private"))
    router.callback_query.register(PrivacyMenu, PrivacyMenuCallback.filter())

    router.message.register(TriggerExport, CMDFilter("export"), ChatTypeFilter("private"))


async def __post_setup__(modules: dict[str, ModuleType]):
    extra_modules = LOADED_MODULES.values() if isinstance(LOADED_MODULES, dict) else LOADED_MODULES
    for module in (*modules.values(), *extra_modules):
        if hasattr(module, "__export__"):
            EXPORTABLE_MODULES.append(module)
