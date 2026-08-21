from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import PRODUCTION, TelegramAPIServer
from aiogram.enums import ParseMode
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import LinkPreviewOptions
from redis.asyncio import Redis

from .config import CONFIG
from .logger import get_logger
from .utils.redis_event_isolation import RenewableRedisEventIsolation

logger = get_logger(__name__)

bot_api = TelegramAPIServer.from_base(str(CONFIG.botapi_server), is_local=True) if CONFIG.botapi_server else PRODUCTION
session = AiohttpSession(api=bot_api)
logger.info("Using BotAPI server", bot_api=str(bot_api))

bot = Bot(
    token=CONFIG.token.get_secret_value(),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML, link_preview=LinkPreviewOptions(is_disabled=True)),
    session=session,
)
aredis = Redis(host=CONFIG.redis_host, port=CONFIG.redis_port, db=CONFIG.redis_db_states)
fsm_redis = Redis(host=CONFIG.redis_host, port=CONFIG.redis_port, db=CONFIG.redis_db_fsm, single_connection_client=True)
fsm_key_builder = DefaultKeyBuilder(prefix=CONFIG.redis_fsm_key_prefix, with_bot_id=True)
storage = RedisStorage(
    redis=fsm_redis,
    key_builder=fsm_key_builder,
    state_ttl=CONFIG.redis_fsm_state_ttl,
    data_ttl=CONFIG.redis_fsm_data_ttl,
)
events_isolation = RenewableRedisEventIsolation(
    redis=fsm_redis, key_builder=fsm_key_builder, lock_kwargs={"timeout": CONFIG.redis_fsm_lock_timeout}
)
dp = Dispatcher(storage=storage, events_isolation=events_isolation)

__all__ = ("aredis", "bot", "dp", "fsm_redis")
