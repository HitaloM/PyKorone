from types import ModuleType

from aiogram import Router

from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.user_status import IsOP
from sophie_bot.modules.help.callbacks import PMHelpModule
from sophie_bot.modules.help.cmds import ModuleHelp, gather_module_help, HELP_MODULES
from sophie_bot.modules.help.handlers.op import OpCMDSList
from sophie_bot.modules.help.handlers.pm_modules import PMModulesList, PMModuleHelp
from sophie_bot.utils.i18n import lazy_gettext as l_
from sophie_bot.utils.logger import log

router = Router(name="help")


__module_name__ = l_("Help")
__module_emoji__ = "❔"


def __pre_setup__():
    router.message.register(PMModulesList, CMDFilter("newhelp"))
    router.callback_query.register(PMModuleHelp, PMHelpModule.filter())

    router.message.register(OpCMDSList, CMDFilter("op_cmds"), IsOP(True))


def __post_setup__(modules: dict[str, ModuleType]):
    for name, module in modules.items():
        if module_help := gather_module_help(module):
            if name in HELP_MODULES:
                log.debug(f"Module {name} already in help modules, merging")
                module_help.cmds = HELP_MODULES[name].cmds + module_help.cmds

            HELP_MODULES[name] = module_help
