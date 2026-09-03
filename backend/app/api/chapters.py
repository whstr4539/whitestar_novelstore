"""章节接口：阅读（权限校验 + Redis 缓存）/ 购买（事务）"""
from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.deps import get_current_user, get_current_user_optional
from app.database import get_db
from app.models import Chapter, ChapterContent, Novel, ReadingHistory, User
from app.redis_client import get_redis
from app.schemas import ChapterMetaOut, ChapterReadOut, IdParam, Message, PurchaseOut
from app.services.cache import cache_key, delete_keys, get_json, set_json
from app.services.purchase import has_purchased, purchase_chapter

router = APIRouter(prefix="/api/chapters", tags=["章节"])


async def _get_chapter(db: AsyncSession, chapter_id: int) -> Chapter:
    chapter = await db.scalar(
        select(Chapter)
        .options(selectinload(Chapter.content))
        .where(Chapter.id == chapter_id, Chapter.status == 1)  # 已删除章节不可读
    )
    if chapter is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "章节不存在")
    return chapter


def _is_payable(chapter: Chapter) -> bool:
    """是否收费：price > 0 且非试读；is_vip 仅运营标识，price=0 的脏数据视为免费"""
    return float(chapter.price) > 0 and not chapter.is_free


async def _record_history(db: AsyncSession, user_id: int, novel_id: int, chapter_id: int):
    """写阅读记录（UPSERT 语义：每本书只保留一条进度）"""
    await db.execute(
        pg_insert(ReadingHistory)
        .values(user_id=user_id, novel_id=novel_id, chapter_id=chapter_id, progress=0)
        .on_conflict_do_update(
            index_elements=["user_id", "novel_id"],
            set_={"chapter_id": chapter_id, "last_read_at": func.now()},
        )
    )
    await db.commit()


async def _is_owner_or_admin(db: AsyncSession, chapter: Chapter, user: User) -> bool:
    """章节所属作品的作者本人，或管理员，可免购买阅读"""
    if user.role == "admin":
        return True
    if user.role == "author":
        novel = await db.get(Novel, chapter.novel_id)
        return novel is not None and novel.author_id == user.id
    return False


@router.get("/{chapter_id}", response_model=ChapterReadOut, summary="阅读章节（免费直接读，付费需已购）")
async def read_chapter(
    chapter_id: IdParam,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    user: User | None = Depends(get_current_user_optional),
):
    # 缓存只存免费章（purchased 恒 False），匿名/登录均可命中；付费章从不入缓存
    cache_hit = await get_json(redis, cache_key("chapter", chapter_id))

    if cache_hit is not None:
        cache_hit["purchased"] = False
        if user:
            await _record_history(db, user.id, cache_hit["novel_id"], chapter_id)
        return cache_hit

    chapter = await _get_chapter(db, chapter_id)

    # 收费章必须已购（作者本人/管理员免购）
    purchased = False
    if _is_payable(chapter):
        if user is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "付费章节需登录后购买")
        if await _is_owner_or_admin(db, chapter, user):
            purchased = True
        else:
            purchased = await has_purchased(db, user.id, chapter_id)
            if not purchased:
                raise HTTPException(
                    status.HTTP_402_PAYMENT_REQUIRED,
                    detail={
                        "message": f"该章节为付费章节（{chapter.price} 书币），购买后解锁",
                        "chapter": ChapterMetaOut.model_validate(chapter).model_dump(mode="json"),
                    },
                )

    content = chapter.content.content if chapter.content else "（本章暂无正文）"

    if user:
        await _record_history(db, user.id, chapter.novel_id, chapter.id)

    result = ChapterReadOut(
        chapter=ChapterMetaOut.model_validate(chapter),
        content=content,
        purchased=purchased,
        novel_id=chapter.novel_id,
    )
    if not _is_payable(chapter):
        await set_json(redis, cache_key("chapter", chapter_id), result.model_dump(mode="json"), settings.CACHE_TTL_CHAPTER)
    return result


@router.post("/{chapter_id}/purchase", response_model=PurchaseOut, summary="购买章节（事务扣费）")
async def buy_chapter(
    chapter_id: IdParam,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    user: User = Depends(get_current_user),
):
    chapter = await _get_chapter(db, chapter_id)
    if not _is_payable(chapter):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "免费章节无需购买")

    purchase, balance_after = await purchase_chapter(db, user.id, chapter)
    await db.commit()
    await db.refresh(purchase)

    await delete_keys(redis, cache_key("chapter", chapter_id))

    return PurchaseOut(
        chapter_id=chapter.id,
        price_paid=float(purchase.price_paid),
        balance_after=balance_after,
        purchased_at=purchase.purchased_at,
    )


@router.get("/{chapter_id}/status", summary="查询章节购买状态")
async def chapter_status(
    chapter_id: IdParam,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    chapter = await _get_chapter(db, chapter_id)
    return {
        "chapter_id": chapter.id,
        "is_vip": chapter.is_vip,
        "price": float(chapter.price),
        "is_free": chapter.is_free,
        "purchased": await has_purchased(db, user.id, chapter_id),
    }
