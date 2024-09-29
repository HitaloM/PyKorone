from types import ModuleType

from aiogram import Router

from sophie_bot.utils.i18n import lazy_gettext as l_

from ...filters.chat_status import ChatTypeFilter
from ...filters.cmd import CMDFilter
from ..legacy_modules import LOADED_LEGACY_MODULES
from .callbacks import PrivacyMenuCallback
from .handlers.export import EXPORTABLE_MODULES, TriggerExport
from .handlers.privacy import PrivacyMenu

router = Router(name="info")


__module_name__ = l_("Privacy")
__module_emoji__ = "🕵️‍♂️️"
__module_description__ = l_("Provides helpful information")


def __pre_setup__():
    router.message.register(PrivacyMenu, CMDFilter("privacy"), ChatTypeFilter("private"))
    router.callback_query.register(PrivacyMenu, PrivacyMenuCallback.filter())

    router.message.register(TriggerExport, CMDFilter("export"))


def __post_setup__(modules: dict[str, ModuleType]):
    for module in (*modules.values(), *LOADED_LEGACY_MODULES):
        if hasattr(module, "__export__"):
            EXPORTABLE_MODULES.append(module)
