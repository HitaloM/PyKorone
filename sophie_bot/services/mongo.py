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

import sys
from contextvars import ContextVar

from motor import motor_asyncio
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

from sophie_bot import log
from sophie_bot.config import CONFIG

mongodb = MongoClient(CONFIG.mongo_host, CONFIG.mongo_port)[CONFIG.mongo_db]

motor = ContextVar('motor')
db = ContextVar('motor_db')


def get_db():
    motor.set(motor_asyncio.AsyncIOMotorClient(CONFIG.mongo_host, CONFIG.mongo_port))
    db.set(motor.get()[CONFIG.mongo_db])


async def test_db():
    try:
        await motor.get().server_info()
    except ServerSelectionTimeoutError:
        sys.exit(log.critical("Can't connect to mongodb! Exiting..."))
