import asyncio
from importlib import import_module

from sophie_bot import CONFIG, dp

from ...utils.logger import log
from .modules import ALL_MODULES, LOADED_LEGACY_MODULES


async def before_srv_task():
    loop = asyncio.get_event_loop()
    for module in [m for m in LOADED_LEGACY_MODULES if hasattr(m, "__before_serving__")]:
        log.debug(f"Before serving: {module.__name__}")
        await module.__before_serving__(loop)


def __pre_setup__():
    modules = CONFIG.modules_load if len(CONFIG.modules_load) > 0 and "*" not in CONFIG.modules_load else ALL_MODULES
    modules = [x for x in modules if x not in CONFIG.modules_not_load]

    from .utils.register import legacy_states_router

    log.info("Legacy modules: to load: %s", str(modules))
    for module_name in modules:
        log.debug(f"Legacy modules: Importing <d><n>{module_name}</></>")
        imported_module = import_module(f"sophie_bot.modules.legacy_modules.modules.{module_name}")
        LOADED_LEGACY_MODULES.append(imported_module)
        legacy_states_router.include_router(imported_module.router)

    log.info("Legacy modules: Modules loaded!")

    asyncio.get_event_loop().run_until_complete(before_srv_task())

    log.info("Legacy modules: Pre setup")

    dp.include_router(legacy_states_router)


def __post_setup__(_):
    from .utils.register import legacy_modules_router

    log.info("Legacy modules: Post setup")
    dp.include_router(legacy_modules_router)

    from sophie_bot.modules.help import HELP_MODULES, gather_module_help

    for module in LOADED_LEGACY_MODULES:
        module_name = module.__name__.split(".")[-1]
        if help := gather_module_help(module):
            HELP_MODULES[module_name] = help
