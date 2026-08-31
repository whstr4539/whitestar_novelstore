"""Redis 缓存封装：缓存穿透保护 + JSON 序列化"""
import json

from redis.asyncio import Redis

from app.config import settings


async def get_json(redis: Redis, key: str):
    """读缓存，无则返回 None。Redis 故障降级为未命中，回源数据库，不抛错。"""
    try:
        raw = await redis.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None
    except Exception:  # noqa: BLE001 Redis 不可用时按未命中处理
        return None


async def set_json(redis: Redis, key: str, value, ttl: int | None = None):
    """写缓存（自动 JSON 序列化）。写失败不影响主流程。"""
    ttl = ttl if ttl is not None else settings.CACHE_TTL_NOVEL_DETAIL
    try:
        await redis.set(key, json.dumps(value, ensure_ascii=False, default=str), ex=ttl)
    except Exception:  # noqa: BLE001 缓存写失败降级
        pass


async def delete_keys(redis: Redis, *keys: str):
    """批量删除缓存。失效失败不影响主流程（已提交事务不应因此返回 500）。"""
    if keys:
        try:
            await redis.delete(*keys)
        except Exception:  # noqa: BLE001 缓存失效失败降级
            pass


def cache_key(*parts) -> str:
    """生成缓存 key：cache:novel:1 格式"""
    return ":".join(["cache", *map(str, parts)])
