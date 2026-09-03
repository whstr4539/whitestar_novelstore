"""书架接口：收藏 / 取消收藏 / 书架列表 / 阅读历史"""
from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user
from app.database import get_db
from app.models import Chapter, Favorite, Novel, ReadingHistory, User
from app.redis_client import get_redis
from app.schemas import BookshelfItem, BookshelfOut, IdParam, Message, NovelOut, ProgressIn
from app.services.cache import cache_key, delete_keys

router = APIRouter(prefix="/api/bookshelf", tags=["书架"])


@router.get("", response_model=BookshelfOut, summary="我的书架")
async def my_bookshelf(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    rows = (
        await db.execute(
            select(Favorite, Novel)
            .join(Novel, Novel.id == Favorite.novel_id)
            .options(selectinload(Novel.category), selectinload(Novel.author))
            .where(Favorite.user_id == user.id)
            .order_by(Favorite.added_at.desc())
        )
    ).all()
    items = [
        BookshelfItem(novel=NovelOut.model_validate(n), added_at=f.added_at)
        for f, n in rows
    ]
    return BookshelfOut(items=items)


@router.post("/{novel_id}", response_model=Message, summary="加入书架")
async def add_favorite(
    novel_id: IdParam,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    user: User = Depends(get_current_user),
):
    novel = await db.get(Novel, novel_id)
    if novel is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "小说不存在")
    exists = await db.scalar(
        select(Favorite).where(Favorite.user_id == user.id, Favorite.novel_id == novel_id)
    )
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "已在书架中")
    db.add(Favorite(user_id=user.id, novel_id=novel_id))
    novel.total_favorites += 1
    try:
        await db.commit()
    except IntegrityError:
        # 并发重复收藏：唯一约束兜底
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "已在书架中")
    await delete_keys(redis, cache_key("novel", novel_id))
    return Message(detail="收藏成功")


@router.delete("/{novel_id}", response_model=Message, summary="移出书架")
async def remove_favorite(
    novel_id: IdParam,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        delete(Favorite).where(Favorite.user_id == user.id, Favorite.novel_id == novel_id)
    )
    if result.rowcount == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "不在书架中")
    novel = await db.get(Novel, novel_id)
    if novel and novel.total_favorites > 0:
        novel.total_favorites -= 1
    await db.commit()
    await delete_keys(redis, cache_key("novel", novel_id))
    return Message(detail="已移出书架")


@router.get("/history/list", response_model=BookshelfOut, summary="阅读历史")
async def reading_history(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    rows = (
        await db.execute(
            select(ReadingHistory, Novel)
            .join(Novel, Novel.id == ReadingHistory.novel_id)
            .options(selectinload(Novel.category), selectinload(Novel.author))
            .where(ReadingHistory.user_id == user.id)
            .order_by(ReadingHistory.last_read_at.desc())
        )
    ).all()
    items = [
        BookshelfItem(novel=NovelOut.model_validate(n), added_at=h.last_read_at, chapter_id=h.chapter_id)
        for h, n in rows
    ]
    return BookshelfOut(items=items)


@router.put("/progress", response_model=Message, summary="上报阅读进度（每本书只存一条）")
async def update_progress(
    data: ProgressIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # 校验章节归属，防 FK 500 与错位进度
    novel = await db.get(Novel, data.novel_id)
    if novel is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "小说不存在")
    chapter = await db.get(Chapter, data.chapter_id)
    if chapter is None or chapter.novel_id != data.novel_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "章节不存在或不属于该小说")

    # UPSERT：同一用户+同一本书只保留一条进度
    await db.execute(
        pg_insert(ReadingHistory)
        .values(
            user_id=user.id,
            novel_id=data.novel_id,
            chapter_id=data.chapter_id,
            progress=data.progress,
        )
        .on_conflict_do_update(
            index_elements=["user_id", "novel_id"],
            set_={"chapter_id": data.chapter_id, "progress": data.progress, "last_read_at": func.now()},
        )
    )
    await db.commit()
    return Message(detail="进度已保存")
