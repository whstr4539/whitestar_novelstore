"""公告接口：列表（公开）/ 发布与删除（管理员）"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin
from app.database import get_db
from app.models import Notice, User
from app.schemas import Message, NoticeIn, NoticeOut

router = APIRouter(prefix="/api/notices", tags=["公告"])


@router.get("", response_model=list[NoticeOut], summary="公告列表（公开）")
async def list_notices(db: AsyncSession = Depends(get_db)):
    notices = (
        await db.scalars(
            select(Notice).where(Notice.is_active == True).order_by(Notice.created_at.desc())  # noqa: E712
        )
    ).all()
    return [NoticeOut.model_validate(n) for n in notices]


@router.post("", response_model=NoticeOut, status_code=201, summary="发布公告（管理员）")
async def create_notice(
    data: NoticeIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    notice = Notice(title=data.title, content=data.content)
    db.add(notice)
    await db.commit()
    await db.refresh(notice)
    return NoticeOut.model_validate(notice)


@router.delete("/{notice_id}", response_model=Message, summary="删除公告（管理员）")
async def delete_notice(
    notice_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    notice = await db.get(Notice, notice_id)
    if notice is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "公告不存在")
    await db.delete(notice)
    await db.commit()
    return Message(detail="删除成功")
