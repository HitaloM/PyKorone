# Copyright (C) 2018 - 2020 MrYacha. All rights reserved. Source code available under the AGPL.
# Copyright (C) 2019 Aiogram
#
# This file is part of SophieBot.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
from importlib import import_module

from sophie_bot import dp, bot
from sophie_bot.config import CONFIG
from sophie_bot.legacy_modules import ALL_MODULES, LOADED_MODULES
from sophie_bot.middlewares import enable_middlewares
from sophie_bot.modules import load_modules
from sophie_bot.services.apscheduller import start_apscheduller
from sophie_bot.services.db import init_db, test_db
from sophie_bot.services.telethon import start_telethon
from sophie_bot.utils.logger import log

enable_middlewares()

if CONFIG.debug_mode:
    pass
    # log.debug("Enabling logging middleware.")
    # dp.middleware.setup(LoggingMiddleware())

# Load new modules
load_modules(dp, ['*'], CONFIG.modules_not_load)

# Load legacy modules
if len(CONFIG.modules_load) > 0:
    modules = CONFIG.modules_load
else:
    modules = ALL_MODULES

modules = [x for x in modules if x not in CONFIG.modules_not_load]

log.info("Legacy modules: to load: %s", str(modules))
for module_name in modules:
    log.debug(f"Legacy modules: Importing <d><n>{module_name}</></>")
    imported_module = import_module("sophie_bot.legacy_modules." + module_name)
    LOADED_MODULES.append(imported_module)
log.info("Legacy modules: Modules loaded!")

# Import misc stuff
if not CONFIG.debug_mode:
    import_module("sophie_bot.utils.sentry")


async def before_srv_task():
    loop = asyncio.get_event_loop()
    for module in [m for m in LOADED_MODULES if hasattr(m, '__before_serving__')]:
        log.debug('Before serving: ' + module.__name__)
        await module.__before_serving__(loop)


@dp.startup()
async def start():
    await init_db()
    await test_db()

    await start_telethon()

    await start_apscheduller()

    log.debug("Starting before serving task for all modules...")
    await before_srv_task()

    if CONFIG.debug_mode:
        log.debug("Waiting 2 seconds...")
        await asyncio.sleep(2)


async def main() -> None:
    await dp.start_polling(bot)


asyncio.run(main())
