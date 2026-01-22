from asyncio import gather

from aiogram import Dispatcher

from sophie_bot.config import CONFIG
from sophie_bot.db.models.chat import ChatModel
from sophie_bot.modules import load_modules
from sophie_bot.services.bot import bot
from sophie_bot.services.db import init_db
from sophie_bot.utils.logger import log


async def ensure_bot_in_db() -> None:
    bot_user = await bot.get_me()
    await ChatModel.upsert_user(bot_user)
    log.info("Bot user ensured in DB", bot_id=bot_user.id, username=bot_user.username)


async def start_init(dp: Dispatcher) -> None:
    await init_db()
    await gather(ensure_bot_in_db(), load_modules(dp, ["*"], CONFIG.modules_not_load))
