"""用户接口：公开主页 + 编辑个人资料"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models import Novel, User
from app.schemas import UserOut, UserUpdateIn

router = APIRouter(prefix="/api/users", tags=["用户"])


# 注意：/me 必须注册在 /{user_id} 之前，否则 "me" 会被解析为 user_id
@router.put("/me", response_model=UserOut, summary="编辑个人资料（昵称/邮箱/头像）")
async def update_me(
    data: UserUpdateIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if data.nickname is not None:
        nickname = data.nickname.strip()
        if not nickname:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "昵称不能为空")
        user.nickname = nickname
    if data.email is not None:
        email = data.email.strip() or None
        # 邮箱唯一性校验（排除自己）
        if email:
            exists = await db.scalar(
                select(User.id).where(User.email == email, User.id != user.id)
            )
            if exists:
                raise HTTPException(status.HTTP_409_CONFLICT, "邮箱已被其他用户使用")
        user.email = email
    if data.avatar is not None:
        user.avatar = data.avatar.strip() or None

    await db.commit()
    await db.refresh(user)
    return user


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
