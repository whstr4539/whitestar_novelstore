"""FastAPI 依赖：认证"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.database import get_db
from app.models import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """解析 Bearer Token 得到当前用户"""
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "未登录")
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token 无效或已过期")
    user = await db.scalar(select(User).where(User.id == int(payload["sub"])))
    if user is None or user.status != 1:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户不存在或已被封禁")
    return user


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """可选登录：未带 token 返回 None；带无效 token 仍拒绝（401）"""
    if credentials is None:
        return None
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token 无效或已过期")
    user = await db.scalar(select(User).where(User.id == int(payload["sub"])))
    if user is None or user.status != 1:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户不存在或已被封禁")
    return user


async def get_current_author(user: User = Depends(get_current_user)) -> User:
    """仅作者/管理员可访问"""
    if user.role not in ("author", "admin"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "需要作者权限")
    return user


async def get_current_admin(user: User = Depends(get_current_user)) -> User:
    """仅管理员可访问"""
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "需要管理员权限")
    return user
