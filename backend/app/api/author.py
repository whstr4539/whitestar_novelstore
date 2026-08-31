"""作者后台：创建小说 / 发布章节（触发器自动更新作品统计）/ 修改章节 / 我的作品"""
from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_author
from app.database import get_db
from app.models import Chapter, ChapterContent, ChapterPurchase, Novel, Reward, User
from app.redis_client import get_redis
from app.schemas import (
    AuthorNovelIn,
    AuthorStatsOut,
    ChapterCreateIn,
    ChapterCreatedOut,
    ChapterUpdateIn,
    Message,
    NovelOut,
)
from app.services.cache import cache_key, delete_keys

router = APIRouter(prefix="/api/author", tags=["作者后台"])


def _check_owner(novel: Novel, user: User):
    """校验作品归属：作者本人或管理员"""
    if novel.author_id != user.id and user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "无权操作他人作品")


@router.get("/my-novels", response_model=list[NovelOut], summary="我的作品")
async def my_novels(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_author)
):
    novels = (
        await db.scalars(
            select(Novel)
            .options(selectinload(Novel.category), selectinload(Novel.author))
            .where(Novel.author_id == user.id)
            .order_by(Novel.updated_at.desc())
        )
    ).all()
    return [NovelOut.model_validate(n) for n in novels]


@router.get("/stats", response_model=AuthorStatsOut, summary="写作台概览（作品数/点击/订阅/打赏收入）")
async def author_stats(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_author),
):
    """作者全景统计：作品数、总点击、章节总数、订阅收入、打赏收入（一次聚合查询）"""
    # 作品维度：作品数 / 总点击 / 章节总数 / 总字数（chapter_count 由触发器维护的冗余列）
    novel_count, total_views, chapter_count, word_count = (
        await db.execute(
            select(
                func.count(Novel.id),
                func.coalesce(func.sum(Novel.total_views), 0),
                func.coalesce(func.sum(Novel.chapter_count), 0),
                func.coalesce(func.sum(Novel.word_count), 0),
            ).where(Novel.author_id == user.id)
        )
    ).one()

    # 订阅收入：该书所有章节的订阅成交额
    chapter_revenue, purchase_count = (
        await db.execute(
            select(
                func.coalesce(func.sum(ChapterPurchase.price_paid), 0),
                func.count(ChapterPurchase.id),
            )
            .join(Chapter, Chapter.id == ChapterPurchase.chapter_id)
            .join(Novel, Novel.id == Chapter.novel_id)
            .where(Novel.author_id == user.id)
        )
    ).one()

    # 打赏收入
    reward_revenue, reward_count = (
        await db.execute(
            select(
                func.coalesce(func.sum(Reward.amount), 0),
                func.count(Reward.id),
            )
            .join(Novel, Novel.id == Reward.novel_id)
            .where(Novel.author_id == user.id)
        )
    ).one()

    return AuthorStatsOut(
        novel_count=novel_count,
        total_views=total_views,
        chapter_count=chapter_count,
        word_count=word_count,
        chapter_revenue=float(chapter_revenue),
        reward_revenue=float(reward_revenue),
        total_revenue=float(chapter_revenue) + float(reward_revenue),
        purchase_count=purchase_count,
        reward_count=reward_count,
    )


@router.get("/novels/{novel_id}/earnings", summary="作品收益统计（订阅/打赏收入）")
async def novel_earnings(
    novel_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_author),
):
    from app.models import ChapterPurchase, Reward, Chapter

    novel = await db.get(Novel, novel_id)
    if novel is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "作品不存在")
    _check_owner(novel, user)

    # 订阅收入：该书所有章节的订阅成交额
    revenue = await db.scalar(
        select(func.coalesce(func.sum(ChapterPurchase.price_paid), 0))
        .join(Chapter, Chapter.id == ChapterPurchase.chapter_id)
        .where(Chapter.novel_id == novel_id)
    )
    # 打赏收入：该书被打赏的书币
    reward_total = await db.scalar(
        select(func.coalesce(func.sum(Reward.amount), 0)).where(Reward.novel_id == novel_id)
    )
    # 订阅笔数
    purchase_count = await db.scalar(
        select(func.count()).select_from(ChapterPurchase)
        .join(Chapter, Chapter.id == ChapterPurchase.chapter_id)
        .where(Chapter.novel_id == novel_id)
    )
    # 打赏笔数
    reward_count = await db.scalar(
        select(func.count()).select_from(Reward).where(Reward.novel_id == novel_id)
    )
    return {
        "novel_id": novel_id,
        "title": novel.title,
        "chapter_revenue": float(revenue or 0),
        "reward_revenue": float(reward_total or 0),
        "total_revenue": float(revenue or 0) + float(reward_total or 0),
        "purchase_count": int(purchase_count or 0),
        "reward_count": int(reward_count or 0),
    }


@router.post("/novels", response_model=NovelOut, status_code=201, summary="创建小说")
async def create_novel(
    data: AuthorNovelIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_author),
):
    novel = Novel(
        author_id=user.id,
        title=data.title,
        intro=data.intro,
        cover_url=data.cover_url,
        category_id=data.category_id,
        status="serializing",
    )
    db.add(novel)
    await db.commit()
    # 重新查询并预加载关联（避免异步懒加载报错）
    novel = await db.scalar(
        select(Novel)
        .options(selectinload(Novel.category), selectinload(Novel.author))
        .where(Novel.id == novel.id)
    )
    return NovelOut.model_validate(novel)


@router.post("/novels/{novel_id}/chapters", response_model=ChapterCreatedOut, status_code=201, summary="发布章节（自动更新作品章数/字数）")
async def publish_chapter(
    novel_id: int,
    data: ChapterCreateIn,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    user: User = Depends(get_current_author),
):
    novel = await db.get(Novel, novel_id)
    if novel is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "小说不存在")
    _check_owner(novel, user)

    # 价格 > 0 即为付费章节；不接受负价
    if (data.price or 0) < 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "价格不能为负")
    # 下一章序号 = 当前最大章号 + 1
    max_no = await db.scalar(
        select(func.max(Chapter.chapter_no)).where(Chapter.novel_id == novel_id)
    )
    chapter_no = (max_no or 0) + 1

    word_count = len(data.content)  # 中文字符数作为字数

    # 章节元信息 + 正文（同一事务，正文 1:1 拆分表）
    chapter = Chapter(
        novel_id=novel_id,
        chapter_no=chapter_no,
        title=data.title,
        price=data.price,
        is_free=data.is_free,
        word_count=word_count,
    )
    db.add(chapter)
    await db.flush()  # 拿到 chapter.id
    db.add(ChapterContent(chapter_id=chapter.id, content=data.content))

    # 触发器 trg_chapter_insert 会自动更新 novels.chapter_count / word_count
    await db.commit()
    await db.refresh(novel)

    # 新章节发布：失效该小说相关缓存
    await delete_keys(redis, cache_key("novel", novel_id), cache_key("novels", "hot"))

    return ChapterCreatedOut(
        id=chapter.id,
        novel_id=novel_id,
        chapter_no=chapter_no,
        title=chapter.title,
        word_count=word_count,
        novel_chapter_count=novel.chapter_count,
        novel_word_count=novel.word_count,
    )


@router.put("/chapters/{chapter_id}", response_model=Message, summary="修改章节（标题/正文/价格）")
async def update_chapter(
    chapter_id: int,
    data: ChapterUpdateIn,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    user: User = Depends(get_current_author),
):
    chapter = await db.get(Chapter, chapter_id)
    if chapter is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "章节不存在")
    novel = await db.get(Novel, chapter.novel_id)
    _check_owner(novel, user)

    changed = False
    if data.title is not None:
        chapter.title = data.title
        changed = True
    if data.price is not None:
        chapter.price = data.price
        changed = True
    if data.is_free is not None:
        chapter.is_free = data.is_free
        changed = True

    # 校验：价格不能为负（付费与否只看价格）
    if float(chapter.price or 0) < 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "价格不能为负")

    if data.content is not None:
        content = await db.get(ChapterContent, chapter_id)
        if content is None:
            content = ChapterContent(chapter_id=chapter_id, content="")
            db.add(content)
        content.content = data.content
        chapter.word_count = len(data.content)
        changed = True

    if changed:
        # 重新聚合全书总字数（INSERT 触发器只覆盖发布章节场景）
        novel.word_count = await db.scalar(
            select(func.coalesce(func.sum(Chapter.word_count), 0)).where(
                Chapter.novel_id == novel.id
            )
        )
        await db.commit()
        # 正文/价格变化：清章节缓存
        await delete_keys(redis, cache_key("chapter", chapter_id), cache_key("novel", chapter.novel_id))
    return Message(detail="章节已更新")
