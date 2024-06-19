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
from sophie_bot.middlewares import enable_middlewares
from sophie_bot.modules import load_modules
from sophie_bot.services.apscheduller import start_apscheduller
from sophie_bot.services.db import init_db, test_db
from sophie_bot.services.telethon import start_telethon

enable_middlewares()
load_modules(dp, ['*'], CONFIG.modules_not_load)

# Import misc stuff
if not CONFIG.debug_mode:
    import_module("sophie_bot.utils.sentry")


@dp.startup()
async def start():
    await init_db()
    await test_db()

    await start_telethon()
    await start_apscheduller()


async def main() -> None:
    await dp.start_polling(bot)


asyncio.run(main())
