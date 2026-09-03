"""书评评分接口：一人一书一评（UPSERT），提交后重算 novels.score"""
from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user
from app.database import get_db
from app.models import Novel, NovelReview, User
from app.redis_client import get_redis
from app.schemas import IdParam, Message, ReviewIn, ReviewOut
from app.services.cache import cache_key, delete_keys

router = APIRouter(prefix="/api/novels/{novel_id}/reviews", tags=["书评"])


async def _recalc_score(db, novel_id: int):
    """重算小说均分：AVG(rating) 聚合 → 写回 novels.score"""
    avg = await db.scalar(
        select(func.avg(NovelReview.rating)).where(NovelReview.novel_id == novel_id)
    )
    novel = await db.get(Novel, novel_id)
    if novel is not None:
        novel.score = round(float(avg), 1) if avg else 0
    return novel


@router.get("", response_model=list[ReviewOut], summary="评分列表")
async def list_reviews(novel_id: IdParam, db: AsyncSession = Depends(get_db)):
    if await db.get(Novel, novel_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "小说不存在")
    reviews = (
        await db.scalars(
            select(NovelReview)
            .options(selectinload(NovelReview.user))
            .where(NovelReview.novel_id == novel_id)
            .order_by(NovelReview.created_at.desc())
        )
    ).all()
    return [ReviewOut.model_validate(r) for r in reviews]


@router.post("", response_model=ReviewOut, status_code=201, summary="提交/更新评分（一人一书一评）")
async def submit_review(
    novel_id: IdParam,
    data: ReviewIn,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    user: User = Depends(get_current_user),
):
    if await db.get(Novel, novel_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "小说不存在")

    # UPSERT：同一用户对同一书重复评分 → 更新
    stmt = (
        pg_insert(NovelReview)
        .values(user_id=user.id, novel_id=novel_id, rating=data.rating, content=data.content)
        .on_conflict_do_update(
            index_elements=["user_id", "novel_id"],
            set_={"rating": data.rating, "content": data.content},
        )
        .returning(NovelReview.id)
    )
    review_id = await db.scalar(stmt)

    await _recalc_score(db, novel_id)
    await db.commit()

    # 均分已回写，失效详情缓存
    await delete_keys(redis, cache_key("novel", novel_id))

    review = await db.scalar(
        select(NovelReview)
        .options(selectinload(NovelReview.user))
        .where(NovelReview.id == review_id)
    )
    return ReviewOut.model_validate(review)


@router.delete("/{review_id}", response_model=Message, summary="删除评分（本人或管理员）")
async def delete_review(
    novel_id: IdParam,
    review_id: IdParam,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    user: User = Depends(get_current_user),
):
    review = await db.get(NovelReview, review_id)
    if review is None or review.novel_id != novel_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "评分不存在")
    if review.user_id != user.id and user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "只能删除自己的评分")
    await db.delete(review)
    await _recalc_score(db, novel_id)
    await db.commit()
    await delete_keys(redis, cache_key("novel", novel_id))
    return Message(detail="删除成功")
