"""用户公开信息：个人主页展示"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Novel, User
from app.schemas import UserOut

router = APIRouter(prefix="/api/users", tags=["用户"])


@router.get("/{user_id}", summary="用户公开主页信息（作品数/收藏数/注册时间）")
async def get_user_profile(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if user is None or user.status != 1:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "用户不存在")

    novel_count = await db.scalar(
        select(func.count()).select_from(Novel).where(Novel.author_id == user_id)
    )
    views = await db.scalar(
        select(func.sum(Novel.total_views)).where(Novel.author_id == user_id)
    )

    return {
        **UserOut.model_validate(user).model_dump(),
        "novel_count": novel_count or 0,
        "author_total_views": int(views or 0),
    }
