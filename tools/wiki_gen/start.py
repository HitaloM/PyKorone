import asyncio
from unittest.mock import AsyncMock, patch

from aiogram import Dispatcher

from sophie_bot.config import CONFIG
from sophie_bot.modules import load_modules
from sophie_bot.utils.logger import log


# We need to patch the databases in order to be able to run this in CI without them.
@patch('motor.motor_asyncio.AsyncIOMotorClient')
@patch('redis.asyncio.Redis')
@patch('redis.StrictRedis')
def generate_wiki(mock_redis, mock_aredis, mock_motor):
    mock_aredis.return_value = AsyncMock()
    mock_motor.return_value = AsyncMock()

    log.info("Starting wiki generation task...")
    dp = Dispatcher()

    CONFIG.mode = "nostart"

    asyncio.run(load_modules(dp, ["*"], CONFIG.modules_not_load))

    from tools.wiki_gen.generate_pages import generate_wiki_pages
    asyncio.run(generate_wiki_pages())


if __name__ == '__main__':
    generate_wiki()
