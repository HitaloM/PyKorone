import os
import sys
from typing import TYPE_CHECKING

from redis.asyncio import Redis

from sophie_bot.config import CONFIG

if TYPE_CHECKING:
    aredis: "Redis | FakeAsyncRedis"

if "pytest" in sys.modules or os.environ.get("TESTING") == "1":
    from fakeredis import FakeAsyncRedis

    aredis = FakeAsyncRedis(
        decode_responses=False,
        single_connection_client=True,
    )
else:
    aredis = Redis(
        host=CONFIG.redis_host,
        port=CONFIG.redis_port,
        db=CONFIG.redis_db_states,
        decode_responses=False,
        single_connection_client=True,
    )
