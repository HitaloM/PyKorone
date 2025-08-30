import os
import sys
from typing import TYPE_CHECKING

from redis import StrictRedis
from redis.asyncio import Redis

from sophie_bot.config import CONFIG

if TYPE_CHECKING:
    redis: "StrictRedis | FakeStrictRedis"
    bredis: "StrictRedis | FakeStrictRedis"
    aredis: "Redis | FakeAsyncRedis"

if "pytest" in sys.modules or os.environ.get("TESTING") == "1":
    from fakeredis import FakeAsyncRedis, FakeStrictRedis

    redis = FakeStrictRedis(
        decode_responses=True,
        single_connection_client=True,
    )
    bredis = FakeStrictRedis(
        single_connection_client=True,
    )
    aredis = FakeAsyncRedis(
        decode_responses=True,
        single_connection_client=True,
    )
else:
    redis = StrictRedis(
        host=CONFIG.redis_host,
        port=CONFIG.redis_port,
        db=CONFIG.redis_db_states,
        decode_responses=True,
        max_connections=25,
        single_connection_client=True,
    )
    bredis = StrictRedis(
        host=CONFIG.redis_host,
        port=CONFIG.redis_port,
        db=CONFIG.redis_db_states,
        max_connections=25,
        single_connection_client=True,
    )
    aredis = Redis(
        host=CONFIG.redis_host,
        port=CONFIG.redis_port,
        db=CONFIG.redis_db_states,
        decode_responses=True,
        single_connection_client=True,
    )
