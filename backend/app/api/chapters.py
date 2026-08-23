"""章节接口：阅读（权限校验 + Redis 缓存）/ 购买（事务）"""
from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.deps import get_current_user
from app.database import get_db
from app.models import Chapter, ChapterContent, Novel, ReadingHistory, User
from app.redis_client import get_redis
from app.schemas import ChapterMetaOut, ChapterReadOut, Message, PurchaseOut
from app.services.cache import cache_key, delete_keys, get_json, set_json
from app.services.purchase import has_purchased, purchase_chapter

router = APIRouter(prefix="/api/chapters", tags=["章节"])


async def _get_chapter(db: AsyncSession, chapter_id: int) -> Chapter:
    chapter = await db.scalar(
        select(Chapter)
        .options(selectinload(Chapter.content))
        .where(Chapter.id == chapter_id)
    )
    if chapter is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "章节不存在")
    return chapter


def _is_payable(chapter: Chapter) -> bool:
    """该章是否收费（VIP 或价格>0，且非试读）"""
    return (chapter.is_vip or float(chapter.price) > 0) and not chapter.is_free


@router.get("/{chapter_id}", response_model=ChapterReadOut, summary="阅读章节（免费直接读，VIP 需已购）")
async def read_chapter(
    chapter_id: int,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    user: User | None = Depends(get_current_user),
):
    # 免费章节正文走 Redis 缓存（热章防 DB 压力）
    cache_hit = None
    if not user:
        chapter = await _get_chapter(db, chapter_id)
        if _is_payable(chapter):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "VIP 章节需登录后购买")
    else:
        cache_hit = await get_json(redis, cache_key("chapter", chapter_id))

    if cache_hit is not None:
        # 命中缓存：仍需校验已购
        purchased = True
        if _is_payable_chapter(cache_hit["chapter"]):
            purchased = await has_purchased(db, user.id, chapter_id)
            if not purchased:
                raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, "该章节为 VIP 章节，请先购买")
        return cache_hit

    chapter = await _get_chapter(db, chapter_id)

    # 权限校验：收费章节必须已购（作者本人可看）
    purchased = False
    if _is_payable(chapter):
        if user is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "VIP 章节需登录后购买")
        if user.role == "admin":
            purchased = True
        else:
            purchased = await has_purchased(db, user.id, chapter_id)
            if not purchased:
                raise HTTPException(
                    status.HTTP_402_PAYMENT_REQUIRED,
                    detail={
                        "message": f"该章节为 VIP 章节（{chapter.price} 书币/章），请先购买",
                        "chapter": ChapterMetaOut.model_validate(chapter).model_dump(mode="json"),
                    },
                )

    content = chapter.content.content if chapter.content else "（本章暂无正文）"

    # 写阅读记录（UPSERT 语义：每本书只保留一条进度）
    if user:
        await db.execute(
            pg_insert(ReadingHistory)
            .values(user_id=user.id, novel_id=chapter.novel_id, chapter_id=chapter.id, progress=0)
            .on_conflict_do_update(
                index_elements=["user_id", "novel_id"],
                set_={"chapter_id": chapter.id, "last_read_at": func.now()},
            )
        )
        await db.commit()

    result = ChapterReadOut(
        chapter=ChapterMetaOut.model_validate(chapter),
        content=content,
        purchased=purchased,
        novel_id=chapter.novel_id,
    )
    # 免费章节才写缓存（收费章节正文不缓存，购买后从库读）
    if not _is_payable(chapter):
        await set_json(redis, cache_key("chapter", chapter_id), result.model_dump(mode="json"), settings.CACHE_TTL_CHAPTER)
    return result


def _is_payable_chapter(chapter_dict: dict) -> bool:
    return (chapter_dict.get("is_vip") or float(chapter_dict.get("price") or 0) > 0) and not chapter_dict.get("is_free")


@router.post("/{chapter_id}/purchase", response_model=PurchaseOut, summary="购买章节（事务扣费）")
async def buy_chapter(
    chapter_id: int,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    user: User = Depends(get_current_user),
):
    chapter = await _get_chapter(db, chapter_id)
    if not _is_payable(chapter):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "免费章节无需购买")

    # 核心事务：锁钱包 → 校验余额 → 扣款 → 写订阅记录
    purchase, balance_after = await purchase_chapter(db, user.id, chapter)
    await db.commit()
    await db.refresh(purchase)

    # 清理相关缓存
    await delete_keys(redis, cache_key("chapter", chapter_id))

    return PurchaseOut(
        chapter_id=chapter.id,
        price_paid=float(purchase.price_paid),
        balance_after=balance_after,
        purchased_at=purchase.purchased_at,
    )


@router.get("/{chapter_id}/status", summary="查询章节购买状态")
async def chapter_status(
    chapter_id: int,
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
