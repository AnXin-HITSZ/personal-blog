import redis
from redis.connection import ConnectionPool

from .config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD


redis_pool = ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    decode_responses=True,
    max_connections=10
)

redis_client = redis.Redis(
    connection_pool=redis_pool
)
