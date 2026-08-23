"""星辰书城 API 入口"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api import author, auth, bookshelf, chapters, comments, notices, novels, reviews, rewards, tickets, wallet
from app.config import settings
from app.database import engine
from app.redis_client import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动/关闭钩子：验证数据库与 Redis 连接"""
    # 启动
    try:
        async with engine.connect() as conn:
            await conn.exec_driver_sql("SELECT 1")
        print("[startup] PostgreSQL 连接成功")
    except Exception as e:
        print(f"[startup] PostgreSQL 连接失败: {e}")
    try:
        await redis_client.ping()
        print("[startup] Redis 连接成功")
    except Exception as e:
        print(f"[startup] Redis 连接失败: {e}")
    yield
    # 关闭
    await engine.dispose()
    await redis_client.aclose()


app = FastAPI(
    title=settings.APP_NAME,
    description="网文书城（起点/番茄模式）课程设计后端\n\n技术栈：FastAPI + PostgreSQL + Redis",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS：允许前端 React（开发端口 3000/5173）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由注册
app.include_router(auth.router)
app.include_router(novels.router)
app.include_router(chapters.router)
app.include_router(bookshelf.router)
app.include_router(wallet.router)
app.include_router(comments.router)
app.include_router(reviews.router)
app.include_router(tickets.router)
app.include_router(rewards.router)
app.include_router(author.router)
app.include_router(notices.router)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.get("/api/health", tags=["系统"], summary="健康检查")
async def health():
    return {"status": "ok", "app": settings.APP_NAME}
