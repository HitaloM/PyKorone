from typing import TYPE_CHECKING

from aiogram import Router
from stfu_tg import Doc

from korone.logging import get_logger
from korone.utils.i18n import LazyProxy
from korone.utils.i18n import lazy_gettext as l_

from .handlers.help_group import HelpGroupHandler
from .handlers.op import OpCMDSList
from .handlers.pm_modules import PMModuleHelp, PMModulesList
from .handlers.start_group import StartGroupHandler
from .handlers.start_pm import StartPMHandler
from .stats import help_stats
from .utils.extract_info import HELP_MODULES, gather_module_help

if TYPE_CHECKING:
    from types import ModuleType

router = Router(name="info")

logger = get_logger(__name__)

__module_name__ = l_("Help")
__module_emoji__ = "ℹ️"
__module_description__ = l_("Provides helpful information")
__module_info__ = LazyProxy(lambda: Doc(l_("Get information about available commands and modules in Korone.")))


__handlers__ = (StartPMHandler, HelpGroupHandler, PMModulesList, StartGroupHandler, PMModuleHelp, OpCMDSList)

__stats__ = help_stats


async def __post_setup__(modules: dict[str, ModuleType]) -> None:
    for name, module in modules.items():
        if module_help := await gather_module_help(module):
            if name in HELP_MODULES:
                await logger.adebug(f"Module {name} already in help modules, merging")
                module_help.handlers = HELP_MODULES[name].handlers + module_help.handlers

            HELP_MODULES[name] = module_help
