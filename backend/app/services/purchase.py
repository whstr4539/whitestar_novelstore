"""核心业务：章节订阅扣费（数据库事务）

流程（一次事务）：
1. SELECT ... FOR UPDATE 锁定用户钱包行
2. 校验余额是否足够
3. UPDATE 扣减余额
4. INSERT chapter_purchases 购买记录（唯一约束防重复扣费）
5. COMMIT
"""
from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Chapter, ChapterPurchase, Wallet


async def purchase_chapter(
    db: AsyncSession, user_id: int, chapter: Chapter
) -> tuple[ChapterPurchase, float]:
    """
    购买章节（事务内执行）。
    返回 (购买记录, 扣费后余额)。
    余额不足抛 402，重复购买抛 409。
    """
    # 幂等检查：已购买过直接返回
    existing = await db.scalar(
        select(ChapterPurchase).where(
            ChapterPurchase.user_id == user_id,
            ChapterPurchase.chapter_id == chapter.id,
        )
    )
    if existing:
        wallet = await db.scalar(select(Wallet).where(Wallet.user_id == user_id))
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=f"已购买过本章（第{chapter.chapter_no}章），当前余额 {wallet.balance if wallet else 0} 书币",
        )

    price = float(chapter.price)
    if price <= 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "该章节无需购买（价格为 0）")

    # 1. 行级锁：防止并发扣费超扣
    wallet = await db.scalar(
        select(Wallet).where(Wallet.user_id == user_id).with_for_update()
    )
    if wallet is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "钱包不存在，请先充值")

    # 2. 余额校验
    if float(wallet.balance) < price:
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"余额不足：需 {price} 书币，当前 {wallet.balance} 书币，请先充值",
        )

    # 3. 扣款
    new_balance = float(wallet.balance) - price
    await db.execute(
        update(Wallet)
        .where(Wallet.user_id == user_id)
        .values(balance=new_balance)
    )

    # 4. 写购买记录（唯一约束防并发重复）
    purchase = ChapterPurchase(
        user_id=user_id, chapter_id=chapter.id, price_paid=price
    )
    db.add(purchase)

    # 5. 提交
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "已购买过本章（并发重复请求被拦截）")
    return purchase, new_balance


async def has_purchased(db: AsyncSession, user_id: int, chapter_id: int) -> bool:
    """用户是否已购买某章节"""
    return (
        await db.scalar(
            select(ChapterPurchase.id).where(
                ChapterPurchase.user_id == user_id,
                ChapterPurchase.chapter_id == chapter_id,
            )
        )
        is not None
    )
