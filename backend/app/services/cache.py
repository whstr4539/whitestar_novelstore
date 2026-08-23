"""Redis 缓存封装：缓存穿透保护 + JSON 序列化"""
import json

from redis.asyncio import Redis

from app.config import settings


async def get_json(redis: Redis, key: str):
    """读缓存，无则返回 None"""
    raw = await redis.get(key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


async def set_json(redis: Redis, key: str, value, ttl: int | None = None):
    """写缓存（自动 JSON 序列化）"""
    ttl = ttl if ttl is not None else settings.CACHE_TTL_NOVEL_DETAIL
    await redis.set(key, json.dumps(value, ensure_ascii=False, default=str), ex=ttl)


async def delete_keys(redis: Redis, *keys: str):
    """批量删除缓存"""
    if keys:
        await redis.delete(*keys)


def cache_key(*parts) -> str:
    """生成缓存 key：cache:novel:1 格式"""
    return ":".join(["cache", *map(str, parts)])
