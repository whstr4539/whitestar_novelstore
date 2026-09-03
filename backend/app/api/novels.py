"""小说接口：列表（Redis 缓存热门榜）/ 详情 / 搜索 / 目录"""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from redis.asyncio import Redis
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.models import Category, Novel, User
from app.redis_client import get_redis
from app.schemas import ChapterMetaOut, IdParam, NovelListOut, NovelOut
from app.services.cache import cache_key, get_json, set_json

router = APIRouter(prefix="/api/novels", tags=["小说"])


@router.get("", response_model=NovelListOut, summary="小说列表/搜索")
async def list_novels(
    keyword: str | None = Query(None, description="标题/作者名/简介模糊搜索"),
    category_id: int | None = Query(None, ge=1, le=2**63 - 1, description="分类筛选"),
    sort: str = Query("hot", pattern="^(hot|new|score)$", description="hot热门 new最新 score评分"),
    page: int = Query(1, ge=1, le=10_000_000),
    page_size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    # 热门榜第一页走 Redis 缓存
    if sort == "hot" and page == 1 and not keyword and not category_id:
        cached = await get_json(redis, cache_key("novels", "hot"))
        if cached is not None:
            return cached

    # 分类筛选：若传的是顶级分类（parent_id 为 NULL），则匹配其全部子分类
    category_ids: list[int] | None = None
    if category_id is not None:
        top = await db.get(Category, category_id)
        if top is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "分类不存在")
        if top.parent_id is None:
            sub_ids = (
                await db.scalars(select(Category.id).where(Category.parent_id == category_id))
            ).all()
            category_ids = [category_id, *sub_ids]
        else:
            category_ids = [category_id]

    stmt = select(Novel).options(selectinload(Novel.category), selectinload(Novel.author))
    count_stmt = select(func.count()).select_from(Novel)

    # 已下架作品对公开列表不可见
    stmt = stmt.where(Novel.status != "banned")
    count_stmt = count_stmt.where(Novel.status != "banned")

    if keyword:
        like = f"%{keyword}%"
        # 作者名匹配：作者昵称命中时，其全部作品计入搜索结果
        author_ids = select(User.id).where(User.nickname.ilike(like))
        match = or_(
            Novel.title.ilike(like),
            Novel.intro.ilike(like),
            Novel.author_id.in_(author_ids),
        )
        stmt = stmt.where(match)
        count_stmt = count_stmt.where(match)
    if category_ids is not None:
        stmt = stmt.where(Novel.category_id.in_(category_ids))
        count_stmt = count_stmt.where(Novel.category_id.in_(category_ids))

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
    novel_id: IdParam,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    # 浏览计数：缓存命中与否都 +1（响应返回后异步执行）
    async def _bump_views():
        await db.execute(
            Novel.__table__.update()
            .where(Novel.id == novel_id)
            .values(total_views=Novel.total_views + 1)
        )
        await db.commit()

    cached = await get_json(redis, cache_key("novel", novel_id))
    if cached is not None:
        # 缓存命中仍校验下架状态，避免下架作品在 TTL 内可见
        if cached.get("status") == "banned":
            raise HTTPException(status.HTTP_404_NOT_FOUND, "小说不存在或已下架")
        background_tasks.add_task(_bump_views)
        return cached

    novel = await db.scalar(
        select(Novel)
        .options(selectinload(Novel.category), selectinload(Novel.author))
        .where(Novel.id == novel_id, Novel.status != "banned")
    )
    if novel is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "小说不存在或已下架")

    # 阅读量 +1 后刷新对象，确保写入缓存的是最新值
    await db.execute(
        Novel.__table__.update().where(Novel.id == novel_id).values(total_views=Novel.total_views + 1)
    )
    await db.commit()
    await db.refresh(novel)

    result = NovelOut.model_validate(novel)
    await set_json(redis, cache_key("novel", novel_id), result.model_dump(mode="json"))
    return result


@router.get("/{novel_id}/chapters", response_model=list[ChapterMetaOut], summary="章节目录")
async def get_chapters(novel_id: IdParam, db: AsyncSession = Depends(get_db)):
    from app.models import Chapter

    novel = await db.get(Novel, novel_id)
    if novel is None or novel.status == "banned":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "小说不存在或已下架")
    chapters = (
        await db.scalars(
            select(Chapter).where(Chapter.novel_id == novel_id, Chapter.status == 1).order_by(Chapter.chapter_no)
        )
    ).all()
    return [ChapterMetaOut.model_validate(c) for c in chapters]
