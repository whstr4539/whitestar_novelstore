"""Redis 连接（异步客户端）"""
from redis.asyncio import Redis, from_url

from app.config import settings

redis_client: Redis = from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)


async def get_redis() -> Redis:
    """FastAPI 依赖：注入 Redis 客户端"""
    return redis_client
