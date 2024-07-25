from types import ModuleType

from aiogram import Router

from sophie_bot.utils.i18n import lazy_gettext as l_

from ...filters.chat_status import ChatTypeFilter
from ...filters.cmd import CMDFilter
from ...filters.user_status import IsOP
from ...utils.logger import log
from .callbacks import PMHelpBack, PMHelpModule
from .handlers.op import OpCMDSList
from .handlers.pm_modules import PMModuleHelp, PMModulesList
from .handlers.privacy import PrivacyInfo
from .utils.extract_info import HELP_MODULES, gather_module_help

router = Router(name="info")


__module_name__ = l_("Information")
__module_emoji__ = "ℹ️"
__module_info__ = l_("Provides helpful information")


def __pre_setup__():
    router.message.register(PMModulesList, CMDFilter("help"), ChatTypeFilter("private"))
    router.callback_query.register(PMModulesList, PMHelpBack.filter())

    router.callback_query.register(PMModuleHelp, PMHelpModule.filter())

    router.message.register(OpCMDSList, CMDFilter("op_cmds"), IsOP(True))

    router.message.register(PrivacyInfo, CMDFilter("privacy"), ChatTypeFilter("private"))


def __post_setup__(modules: dict[str, ModuleType]):
    for name, module in modules.items():
        if module_help := gather_module_help(module):
            if name in HELP_MODULES:
                log.debug(f"Module {name} already in help modules, merging")
                module_help.cmds = HELP_MODULES[name].cmds + module_help.cmds

            HELP_MODULES[name] = module_help
