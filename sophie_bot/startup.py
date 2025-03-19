from asyncio import gather

from aiogram import Dispatcher

from sophie_bot.config import CONFIG
from sophie_bot.modules import load_modules
from sophie_bot.services.db import init_db


async def start_init(dp: Dispatcher):
    await gather(init_db(), load_modules(dp, ["*"], CONFIG.modules_not_load))
