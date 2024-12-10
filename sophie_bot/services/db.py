from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from sophie_bot.config import CONFIG
from sophie_bot.db.models import models

motor: AsyncIOMotorClient = AsyncIOMotorClient(CONFIG.mongo_host, CONFIG.mongo_port)
db = motor[CONFIG.mongo_db]


async def init_db():
    await init_beanie(database=db, document_models=models, allow_index_dropping=CONFIG.mongo_allow_index_dropping)  # type: ignore
