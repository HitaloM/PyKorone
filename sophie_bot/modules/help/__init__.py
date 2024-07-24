from types import ModuleType

from aiogram import Router

from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.user_status import IsOP
from sophie_bot.modules.help.cmds import ModuleHelp, gather_module_help
from sophie_bot.modules.help.handlers.op import OpCMDSList
from sophie_bot.utils.i18n import lazy_gettext as l_

router = Router(name="help")


__module_name__ = l_("Help")
__module_emoji__ = "📔"


HELP_MODULES: list[ModuleHelp] = []


def __pre_setup__():
    router.message.register(OpCMDSList, CMDFilter("op_cmds"), IsOP(True))


def __post_setup__(modules: dict[str, ModuleType]):
    HELP_MODULES.extend(x for x in (gather_module_help(module) for module in modules.values()) if x)
