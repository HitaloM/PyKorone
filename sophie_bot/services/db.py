from beanie import init_beanie
from pymongo import AsyncMongoClient

from sophie_bot.config import CONFIG
from sophie_bot.db.models import models

async_mongo: AsyncMongoClient = AsyncMongoClient(CONFIG.mongo_host, CONFIG.mongo_port)
db = async_mongo[CONFIG.mongo_db]


async def init_db():
    await init_beanie(
        database=db,
        document_models=models,
        allow_index_dropping=CONFIG.mongo_allow_index_dropping,
        skip_indexes=CONFIG.mongo_skip_indexes,
    )
