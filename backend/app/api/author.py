"""作者后台：创建小说 / 发布章节（触发器自动更新作品统计）/ 修改章节 / 我的作品"""
from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_author
from app.database import get_db
from app.models import Chapter, ChapterContent, Novel, User
from app.redis_client import get_redis
from app.schemas import (
    AuthorNovelIn,
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
        is_vip=data.is_vip,
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
        is_vip=data.is_vip,
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
    if data.is_vip is not None:
        chapter.is_vip = data.is_vip
        changed = True
    if data.is_free is not None:
        chapter.is_free = data.is_free
        changed = True
    if data.content is not None:
        content = await db.get(ChapterContent, chapter_id)
        if content is None:
            content = ChapterContent(chapter_id=chapter_id, content="")
            db.add(content)
        content.content = data.content
        chapter.word_count = len(data.content)
        changed = True

    if changed:
        await db.commit()
        # 正文/价格变化：清章节缓存
        await delete_keys(redis, cache_key("chapter", chapter_id), cache_key("novel", chapter.novel_id))
    return Message(detail="章节已更新")
