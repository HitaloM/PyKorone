from types import ModuleType

from aiogram import Router

from sophie_bot.utils.i18n import lazy_gettext as l_

from ...filters.cmd import CMDFilter
from ...filters.user_status import IsOP
from ...utils.logger import log
from .callbacks import PMHelpModule
from .handlers.help_group import HelpGroupHandler
from .handlers.op import OpCMDSList
from .handlers.pm_modules import PMModuleHelp, PMModulesList
from .handlers.start_group import StartGroupHandler
from .handlers.start_pm import StartPMHandler
from .stats import __stats__
from .utils.extract_info import HELP_MODULES, gather_module_help

router = Router(name="info")


__module_name__ = l_("Help")
__module_emoji__ = "ℹ️"
__module_description__ = l_("Provides helpful information")
# __exclude_public__ = True


__handlers__ = (StartPMHandler, HelpGroupHandler, PMModulesList, StartGroupHandler)


async def __pre_setup__():
    router.callback_query.register(PMModuleHelp, PMHelpModule.filter())

    router.message.register(OpCMDSList, CMDFilter("op_cmds"), IsOP(True))


async def __post_setup__(modules: dict[str, ModuleType]):
    for name, module in modules.items():
        if module_help := await gather_module_help(module):
            if name in HELP_MODULES:
                log.debug(f"Module {name} already in help modules, merging")
                module_help.handlers = HELP_MODULES[name].handlers + module_help.handlers

            HELP_MODULES[name] = module_help


__all__ = ["__stats__"]
