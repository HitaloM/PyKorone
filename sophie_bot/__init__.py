from importlib import metadata

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.telegram import PRODUCTION, TelegramAPIServer
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from sophie_bot.config import CONFIG
from sophie_bot.utils.logger import log

SOPHIE_VERSION = metadata.version('sophie_bot')

log.info("----------------------")
log.info("|      SophieBot     |")
log.info("----------------------")
log.info("Version: " + SOPHIE_VERSION)

# Support for custom BotAPI servers
bot_api = TelegramAPIServer.from_base(str(CONFIG.botapi_server)) if CONFIG.botapi_server else PRODUCTION

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
