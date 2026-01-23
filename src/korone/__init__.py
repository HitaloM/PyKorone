from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import PRODUCTION, TelegramAPIServer
from aiogram.enums import ParseMode
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.memory import SimpleEventIsolation
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import LinkPreviewOptions
from redis.asyncio import Redis

from .config import CONFIG
from .logging import get_logger

logger = get_logger(__name__)

bot_api = TelegramAPIServer.from_base(str(CONFIG.botapi_server)) if CONFIG.botapi_server else PRODUCTION
session = AiohttpSession(api=bot_api)
logger.info(f"Using BotAPI server: {bot_api}")

bot = Bot(
    token=CONFIG.token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML, link_preview=LinkPreviewOptions(is_disabled=True)),
    session=session,
)
aredis = Redis(host=CONFIG.redis_host, port=CONFIG.redis_port, db=CONFIG.redis_db_states, single_connection_client=True)
storage = RedisStorage(redis=aredis, key_builder=DefaultKeyBuilder(prefix=str(CONFIG.redis_db_fsm)))
dp = Dispatcher(storage=storage, events_isolation=SimpleEventIsolation())
