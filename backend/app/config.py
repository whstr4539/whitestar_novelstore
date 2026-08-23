"""应用配置：从环境变量 / .env 读取"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # 应用
    APP_NAME: str = "星辰书城 API"
    DEBUG: bool = True

    # 数据库（本地开发连宿主机映射端口；容器内用 postgres/redis 主机名）
    DATABASE_URL: str = (
        "postgresql+asyncpg://novel_user:novel_pass_2024@localhost:5432/novel_db"
    )
    REDIS_URL: str = "redis://:redis_pass_2024@localhost:6379/0"

    # JWT
    SECRET_KEY: str = "novel-course-design-secret-key-2024"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 天

    # Redis 缓存 TTL（秒）
    CACHE_TTL_NOVEL_DETAIL: int = 300
    CACHE_TTL_CHAPTER: int = 3600
    CACHE_TTL_HOT_LIST: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
