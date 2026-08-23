"""小说接口：列表（Redis 缓存热门榜）/ 详情 / 搜索 / 目录"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from redis.asyncio import Redis
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.models import Novel
from app.redis_client import get_redis
from app.schemas import ChapterMetaOut, NovelListOut, NovelOut
from app.services.cache import cache_key, get_json, set_json

router = APIRouter(prefix="/api/novels", tags=["小说"])


@router.get("", response_model=NovelListOut, summary="小说列表/搜索")
async def list_novels(
    keyword: str | None = Query(None, description="标题/简介模糊搜索"),
    category_id: int | None = Query(None, description="分类筛选"),
    sort: str = Query("hot", pattern="^(hot|new|score)$", description="hot热门 new最新 score评分"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    # 热门榜第一页走 Redis 缓存
    if sort == "hot" and page == 1 and not keyword and not category_id:
        cached = await get_json(redis, cache_key("novels", "hot"))
        if cached is not None:
            return cached

    stmt = select(Novel).options(selectinload(Novel.category), selectinload(Novel.author))
    count_stmt = select(func.count()).select_from(Novel)

    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(or_(Novel.title.ilike(like), Novel.intro.ilike(like)))
        count_stmt = count_stmt.where(or_(Novel.title.ilike(like), Novel.intro.ilike(like)))
    if category_id:
        stmt = stmt.where(Novel.category_id == category_id)
        count_stmt = count_stmt.where(Novel.category_id == category_id)

    order_map = {
        "hot": Novel.total_views.desc(),
        "new": Novel.created_at.desc(),
        "score": Novel.score.desc(),
    }
    stmt = stmt.order_by(order_map[sort]).offset((page - 1) * page_size).limit(page_size)

    total = await db.scalar(count_stmt)
    novels = (await db.scalars(stmt)).all()
    result = NovelListOut(
        items=[NovelOut.model_validate(n) for n in novels], total=total or 0
    )

    if sort == "hot" and page == 1 and not keyword and not category_id:
        await set_json(redis, cache_key("novels", "hot"), result.model_dump(mode="json"), settings.CACHE_TTL_HOT_LIST)
    return result


@router.get("/{novel_id}", response_model=NovelOut, summary="小说详情（Redis 缓存）")
async def get_novel(
    novel_id: int,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    cached = await get_json(redis, cache_key("novel", novel_id))
    if cached is not None:
        return cached

    novel = await db.scalar(
        select(Novel)
        .options(selectinload(Novel.category), selectinload(Novel.author))
        .where(Novel.id == novel_id)
    )
    if novel is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "小说不存在")

    # 阅读量 +1（异步计数，不阻塞响应）
    await db.execute(Novel.__table__.update().where(Novel.id == novel_id).values(total_views=Novel.total_views + 1))
    await db.commit()

    result = NovelOut.model_validate(novel)
    await set_json(redis, cache_key("novel", novel_id), result.model_dump(mode="json"))
    return result


@router.get("/{novel_id}/chapters", response_model=list[ChapterMetaOut], summary="章节目录")
async def get_chapters(novel_id: int, db: AsyncSession = Depends(get_db)):
    from app.models import Chapter

    novel = await db.get(Novel, novel_id)
    if novel is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "小说不存在")
    chapters = (
        await db.scalars(
            select(Chapter).where(Chapter.novel_id == novel_id, Chapter.status == 1).order_by(Chapter.chapter_no)
        )
    ).all()
    return [ChapterMetaOut.model_validate(c) for c in chapters]
