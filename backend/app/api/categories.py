"""分类接口：公开分类列表（前端导航/发布作品共用，消除硬编码）"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Category
from app.schemas import CategoryOut

router = APIRouter(prefix="/api/categories", tags=["分类"])


@router.get("", response_model=list[CategoryOut], summary="全部分类（含父子层级）")
async def list_categories(db: AsyncSession = Depends(get_db)):
    categories = (
        await db.scalars(select(Category).order_by(Category.id))
    ).all()
    return [CategoryOut.model_validate(c) for c in categories]
