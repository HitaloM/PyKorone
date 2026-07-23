from aiogram import Router
from stfu_tg import Doc

from korone.modules.metadata import ModuleManifest, ModulePackage, ModuleRegistry, ModuleScripts
from korone.utils.i18n import LazyProxy
from korone.utils.i18n import lazy_gettext as l_

from .handlers.help_group import HelpGroupHandler
from .handlers.op import OpCMDSList
from .handlers.pm_modules import PMModuleHelp, PMModulesList
from .handlers.start_group import StartGroupHandler
from .handlers.start_pm import StartPMHandler
from .stats import help_stats
from .utils.extract_info import HELP_MODULES, gather_module_help, reset_help_registry

router = Router(name="info")


async def post_setup(modules: ModuleRegistry) -> None:
    reset_help_registry()

    for name, module in modules.items():
        if module_help := await gather_module_help(module):
            HELP_MODULES[name] = module_help


manifest = ModuleManifest(
    package=ModulePackage(
        name=l_("Help"),
        icon="ℹ️",
        summary=l_("Command guide and module reference"),
        description=LazyProxy(
            lambda: Doc(
                l_("Browse modules, command usage, and availability rules in one place."),
                l_("Open the interactive help menu privately in any chat."),
            )
        ),
    ),
    router=router,
    handlers=(PMModulesList, StartPMHandler, HelpGroupHandler, StartGroupHandler, PMModuleHelp, OpCMDSList),
    scripts=ModuleScripts(post_setup=post_setup),
    stats=help_stats,
)
