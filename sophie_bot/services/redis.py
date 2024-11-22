from redis import StrictRedis
from redis.asyncio import Redis

from sophie_bot.config import CONFIG

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
    single_connection_client=True,
)
