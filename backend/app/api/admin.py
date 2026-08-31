"""管理后台接口（仅管理员）：统计概览 / 用户管理 / 作品管理"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin
from app.database import get_db
from app.models import Chapter, ChapterPurchase, Novel, RechargeOrder, User
from app.schemas import Message, UserOut

router = APIRouter(prefix="/api/admin", tags=["管理后台"])


@router.get("/comments", summary="评论列表（搜索/分页，仅管理员）")
async def admin_comments(
    keyword: str | None = Query(None, description="评论内容模糊搜索"),
    novel_id: int | None = Query(None, description="按作品筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    from app.models import Comment
    from app.schemas import CommentOut
    from sqlalchemy.orm import selectinload

    stmt = select(Comment).options(selectinload(Comment.user))
    count_stmt = select(func.count()).select_from(Comment)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(Comment.content.ilike(like))
        count_stmt = count_stmt.where(Comment.content.ilike(like))
    if novel_id is not None:
        stmt = stmt.where(Comment.novel_id == novel_id)
        count_stmt = count_stmt.where(Comment.novel_id == novel_id)
    total = await db.scalar(count_stmt)
    comments = (
        await db.scalars(
            stmt.order_by(Comment.created_at.desc())
            .offset((page - 1) * page_size).limit(page_size)
        )
    ).all()
    return {"items": [CommentOut.model_validate(c) for c in comments], "total": total or 0}


@router.get("/stats", summary="平台统计概览")
async def admin_stats(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_admin)
):
    user_count = await db.scalar(select(func.count()).select_from(User))
    author_count = await db.scalar(
        select(func.count()).select_from(User).where(User.role == "author")
    )
    novel_count = await db.scalar(select(func.count()).select_from(Novel))
    chapter_count = await db.scalar(select(func.count()).select_from(Chapter))
    views = await db.scalar(select(func.sum(Novel.total_views)))
    revenue = await db.scalar(select(func.sum(ChapterPurchase.price_paid)))
    recharges = await db.scalar(
        select(func.sum(RechargeOrder.amount)).where(RechargeOrder.status == "success")
    )

    return {
        "user_count": user_count or 0,
        "author_count": author_count or 0,
        "novel_count": novel_count or 0,
        "chapter_count": chapter_count or 0,
        "total_views": int(views or 0),
        "total_revenue": float(revenue or 0),
        "total_recharges": float(recharges or 0),
    }


@router.get("/users", summary="用户列表（搜索/分页）")
async def admin_users(
    keyword: str | None = Query(None, description="用户名/昵称模糊搜索"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    stmt = select(User)
    count_stmt = select(func.count()).select_from(User)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(or_(User.username.ilike(like), User.nickname.ilike(like)))
        count_stmt = count_stmt.where(or_(User.username.ilike(like), User.nickname.ilike(like)))
    total = await db.scalar(count_stmt)
    users = (
        await db.scalars(
            stmt.order_by(User.id).offset((page - 1) * page_size).limit(page_size)
        )
    ).all()
    return {
        "items": [UserOut.model_validate(u) for u in users],
        "total": total or 0,
    }


@router.put("/users/{user_id}/status", response_model=Message, summary="封禁/解封用户")
async def admin_set_user_status(
    user_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    target = await db.get(User, user_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "用户不存在")
    if target.id == user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "不能封禁自己")
    target.status = int(body.get("status", 1))
    await db.commit()
    return Message(detail="已封禁" if target.status == 0 else "已解封")


@router.get("/novels", summary="作品列表（状态筛选/搜索）")
async def admin_novels(
    status_filter: str | None = Query(None, alias="status", description="serializing/finished/banned"),
    keyword: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    from app.schemas import NovelOut
    from sqlalchemy.orm import selectinload

    stmt = select(Novel).options(selectinload(Novel.category), selectinload(Novel.author))
    count_stmt = select(func.count()).select_from(Novel)
    if status_filter:
        stmt = stmt.where(Novel.status == status_filter)
        count_stmt = count_stmt.where(Novel.status == status_filter)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(Novel.title.ilike(like))
        count_stmt = count_stmt.where(Novel.title.ilike(like))
    total = await db.scalar(count_stmt)
    novels = (
        await db.scalars(
            stmt.order_by(Novel.id).offset((page - 1) * page_size).limit(page_size)
        )
    ).all()
    return {
        "items": [NovelOut.model_validate(n) for n in novels],
        "total": total or 0,
    }


@router.put("/novels/{novel_id}/status", response_model=Message, summary="下架/恢复作品")
async def admin_set_novel_status(
    novel_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    novel = await db.get(Novel, novel_id)
    if novel is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "作品不存在")
    new_status = body.get("status", "banned")
    if new_status not in ("serializing", "finished", "banned"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "非法状态值")
    novel.status = new_status
    await db.commit()
    labels = {"serializing": "恢复连载", "finished": "标记完结", "banned": "已下架"}
    return Message(detail=labels[new_status])
