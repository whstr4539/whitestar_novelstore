"""打赏接口：从书币钱包扣款（事务：锁钱包→校验→扣款→记打赏）"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user
from app.database import get_db
from app.models import Novel, Reward, User, Wallet
from app.schemas import IdParam, RewardIn, RewardOut

router = APIRouter(prefix="/api/novels/{novel_id}/rewards", tags=["打赏"])


@router.get("", response_model=list[RewardOut], summary="打赏记录")
async def list_rewards(novel_id: IdParam, db: AsyncSession = Depends(get_db)):
    rewards = (
        await db.scalars(
            select(Reward)
            .options(selectinload(Reward.user))
            .where(Reward.novel_id == novel_id)
            .order_by(Reward.created_at.desc())
        )
    ).all()
    return [RewardOut.model_validate(r) for r in rewards]


@router.post("", response_model=RewardOut, status_code=201, summary="打赏（书币，事务扣费）")
async def reward_novel(
    novel_id: IdParam,
    data: RewardIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    novel = await db.get(Novel, novel_id)
    if novel is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "小说不存在")
    if novel.author_id == user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "不能打赏自己的作品")

    # 行锁钱包
    wallet = await db.scalar(
        select(Wallet).where(Wallet.user_id == user.id).with_for_update()
    )
    if wallet is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "钱包不存在，请先充值")

    if float(wallet.balance) < data.amount:
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"余额不足：需 {data.amount} 书币，当前 {wallet.balance} 书币",
        )

    new_balance = float(wallet.balance) - data.amount
    await db.execute(update(Wallet).where(Wallet.user_id == user.id).values(balance=new_balance))

    reward = Reward(user_id=user.id, novel_id=novel_id, amount=data.amount, message=data.message)
    db.add(reward)
    await db.commit()
    await db.refresh(reward)
    reward.user = user
    return RewardOut.model_validate(reward)
