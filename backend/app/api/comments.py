"""评论接口：本章说 / 书评 / 楼中楼 / 点赞"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user
from app.database import get_db
from app.models import Comment, Novel, User
from app.schemas import CommentIn, CommentOut, Message

router = APIRouter(prefix="/api", tags=["评论"])


@router.get("/novels/{novel_id}/comments", response_model=list[CommentOut], summary="评论列表（不传 chapter_id=书评，传了=本章说）")
async def list_comments(
    novel_id: int,
    chapter_id: int | None = Query(None, description="章节 ID，空则返回书评"),
    db: AsyncSession = Depends(get_db),
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
    comments = (await db.scalars(stmt)).all()
    return [CommentOut.model_validate(c) for c in comments]


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
    if data.parent_id is not None:
        parent = await db.get(Comment, data.parent_id)
        if parent is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "被回复的评论不存在")

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


@router.post("/comments/{comment_id}/like", response_model=Message, summary="点赞评论")
async def like_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    comment = await db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "评论不存在")
    await db.execute(update(Comment).where(Comment.id == comment_id).values(likes=Comment.likes + 1))
    await db.commit()
    return Message(detail="点赞成功")
