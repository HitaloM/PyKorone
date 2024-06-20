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

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.telegram import PRODUCTION, TelegramAPIServer
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from sophie_bot.config import CONFIG
from sophie_bot.utils.logger import log
from sophie_bot.versions import SOPHIE_VERSION

log.info("----------------------")
log.info("|      SophieBot     |")
log.info("----------------------")
log.info("Version: " + SOPHIE_VERSION)

# Support for custom BotAPI servers
bot_api = TelegramAPIServer.from_base(CONFIG.botapi_server) if CONFIG.botapi_server else PRODUCTION

# AIOGram
bot = Bot(token=CONFIG.token, default=DefaultBotProperties(parse_mode="html"), server=bot_api)
redis = Redis(
    host=CONFIG.redis_host,
    port=CONFIG.redis_port,
    db=CONFIG.redis_db_states,
    single_connection_client=True,
)
storage = RedisStorage(redis=redis, key_builder=DefaultKeyBuilder(prefix=str(CONFIG.redis_db_fsm)))
dp = Dispatcher(storage=storage)
