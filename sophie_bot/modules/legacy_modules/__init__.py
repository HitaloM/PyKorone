import asyncio
from importlib import import_module

from aiogram import Router

from sophie_bot import CONFIG

from ...utils.logger import log
from .modules import ALL_MODULES, LOADED_MODULES

router = Router(name="legacy_modules")


async def before_srv_task():
    loop = asyncio.get_event_loop()
    for module in [m for m in LOADED_MODULES if hasattr(m, "__before_serving__")]:
        log.debug(f"Before serving: {module.__name__}")
        await module.__before_serving__(loop)


def __pre_setup__():
    modules = CONFIG.modules_load if len(CONFIG.modules_load) > 0 and "*" not in CONFIG.modules_load else ALL_MODULES
    modules = [x for x in modules if x not in CONFIG.modules_not_load]

    log.info("Legacy modules: to load: %s", str(modules))
    for module_name in modules:
        log.debug(f"Legacy modules: Importing <d><n>{module_name}</></>")
        imported_module = import_module(f"sophie_bot.modules.legacy_modules.modules.{module_name}")
        LOADED_MODULES.append(imported_module)
    log.info("Legacy modules: Modules loaded!")

    asyncio.get_event_loop().run_until_complete(before_srv_task())
