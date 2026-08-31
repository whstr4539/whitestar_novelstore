"""评论接口：本章说 / 书评 / 楼中楼 / 点赞"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, get_current_user_optional
from app.database import get_db
from app.models import Chapter, Comment, CommentLike, Novel, User
from app.schemas import CommentIn, CommentLikeOut, CommentOut, Message

router = APIRouter(prefix="/api", tags=["评论"])


@router.get("/novels/{novel_id}/comments", response_model=list[CommentOut], summary="评论列表（不传 chapter_id=书评，传了=本章说）")
async def list_comments(
    novel_id: int,
    chapter_id: int | None = Query(None, description="章节 ID，空则返回书评"),
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
):
    novel = await db.get(Novel, novel_id)
    if novel is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "小说不存在")

    stmt = (
        select(Comment)
        .options(selectinload(Comment.user))
        .where(Comment.novel_id == novel_id, Comment.parent_id.is_(None))
        .order_by(Comment.likes.desc(), Comment.created_at.desc())
    )
    if chapter_id is not None:
        stmt = stmt.where(Comment.chapter_id == chapter_id)
    else:
        # 不传 chapter_id = 书评：排除本章说（chapter_id 非空）
        stmt = stmt.where(Comment.chapter_id.is_(None))
    comments = (await db.scalars(stmt)).all()
    # 当前用户已赞的评论 id 集合（未登录为空）
    liked_ids: set[int] = set()
    if user is not None and comments:
        rows = await db.scalars(
            select(CommentLike.comment_id).where(
                CommentLike.user_id == user.id,
                CommentLike.comment_id.in_([c.id for c in comments]),
            )
        )
        liked_ids = set(rows.all())
    return [
        CommentOut.model_validate(c).model_copy(update={"liked": c.id in liked_ids})
        for c in comments
    ]


@router.post("/novels/{novel_id}/comments", response_model=CommentOut, status_code=201, summary="发表评论（本章说/书评/回复）")
async def create_comment(
    novel_id: int,
    data: CommentIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    novel = await db.get(Novel, novel_id)
    if novel is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "小说不存在")

    # 本章说归属校验：chapter_id 必须存在且属于该作品，避免"错位/跨书本章说"或指向不存在章节（FK 500）
    if data.chapter_id is not None:
        chapter = await db.get(Chapter, data.chapter_id)
        if chapter is None or chapter.novel_id != novel_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "章节不存在或不属于该作品")

    if data.parent_id is not None:
        parent = await db.get(Comment, data.parent_id)
        if parent is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "被回复的评论不存在")
        if parent.novel_id != novel_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "不能跨作品回复评论")
        if parent.parent_id is not None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "仅支持对主评论回复（不支持层叠回复）")

    comment = Comment(
        user_id=user.id,
        novel_id=novel_id,
        chapter_id=data.chapter_id,
        parent_id=data.parent_id,
        content=data.content,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    comment.user = user  # 响应带用户信息
    return CommentOut.model_validate(comment)


@router.get("/comments/{comment_id}/replies", response_model=list[CommentOut], summary="评论的回复列表（楼中楼）")
async def comment_replies(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
):
    """返回某条评论的直接回复（一层），按时间正序"""
    if await db.get(Comment, comment_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "评论不存在")
    replies = (
        await db.scalars(
            select(Comment)
            .options(selectinload(Comment.user))
            .where(Comment.parent_id == comment_id)
            .order_by(Comment.created_at.asc())
        )
    ).all()
    return [CommentOut.model_validate(c) for c in replies]


@router.delete("/comments/{comment_id}", response_model=Message, summary="删除评论（本人或管理员）")
async def delete_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    comment = await db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "评论不存在")
    if comment.user_id != user.id and user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "只能删除自己的评论")
    await db.delete(comment)
    await db.commit()
    return Message(detail="删除成功")


@router.post("/comments/{comment_id}/like", response_model=CommentLikeOut, summary="点赞/取消点赞（一人一赞，再点取消）")
async def like_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    comment = await db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "评论不存在")

    exists = await db.scalar(
        select(CommentLike.id).where(
            CommentLike.comment_id == comment_id, CommentLike.user_id == user.id
        )
    )
    if exists:
        # 已赞 → 取消点赞（防重复：同一用户对同一评论只 +1 / -1）
        await db.execute(
            delete(CommentLike).where(
                CommentLike.comment_id == comment_id, CommentLike.user_id == user.id
            )
        )
        # 原子减一（greatest 钳制下限为 0），避免并发点赞丢更新
        await db.execute(
            update(Comment).where(Comment.id == comment_id).values(
                likes=func.greatest(Comment.likes - 1, 0)
            )
        )
        await db.commit()
        await db.refresh(comment)
        return CommentLikeOut(liked=False, likes=comment.likes)

    # 未赞 → 点赞（唯一约束防并发重复）
    db.add(CommentLike(comment_id=comment_id, user_id=user.id))
    try:
        # 原子加一（UPDATE ... WHERE 行锁，避免并发丢更新）
        await db.execute(
            update(Comment).where(Comment.id == comment_id).values(likes=Comment.likes + 1)
        )
        await db.commit()
    except IntegrityError:
        # 并发重复点赞：唯一约束拦截，按"已赞"返回
        await db.rollback()
        await db.refresh(comment)
        return CommentLikeOut(liked=True, likes=comment.likes)
    await db.refresh(comment)
    return CommentLikeOut(liked=True, likes=comment.likes)


@router.get("/comments/me", response_model=list[CommentOut], summary="我的评论（含作品/章节标题）")
async def my_comments(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.models import Chapter, Novel

    rows = (
        await db.execute(
            select(Comment, Novel.title, Chapter.title)
            .join(Novel, Novel.id == Comment.novel_id)
            .outerjoin(Chapter, Chapter.id == Comment.chapter_id)
            .where(Comment.user_id == user.id)
            .order_by(Comment.created_at.desc())
            .limit(50)
        )
    ).all()
    items = []
    for c, novel_title, chapter_title in rows:
        out = CommentOut.model_validate(c)
        out.novel_title = novel_title
        out.chapter_title = chapter_title
        items.append(out)
    return items
