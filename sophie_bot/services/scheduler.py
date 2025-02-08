import asyncio

from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from sophie_bot import CONFIG

scheduler_loop = asyncio.new_event_loop()
mongo_store = MongoDBJobStore(
    database=CONFIG.mongo_db,
    collection="jobs",
    host=CONFIG.mongo_host,
    port=CONFIG.mongo_port,
)
mem_store = MemoryJobStore()
scheduler = AsyncIOScheduler(event_loop=scheduler_loop, jobstores={"default": mongo_store, "ram": mem_store})
