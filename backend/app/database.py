"""数据库连接：SQLAlchemy 2.0 async + asyncpg"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # 开发时打印 SQL，便于课设展示
    pool_size=10,
    max_overflow=20,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """所有 ORM 模型的基类"""


async def get_db():
    """FastAPI 依赖：每个请求一个会话"""
    async with async_session() as session:
        yield session
