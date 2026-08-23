"""钱包接口：余额查询 / 充值（mock）"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models import RechargeOrder, User, Wallet
from app.schemas import RechargeIn, RechargeOut, WalletOut

router = APIRouter(prefix="/api/wallet", tags=["钱包"])


def _gen_order_no() -> str:
    """生成业务订单号：R + 时间戳 + 随机数"""
    import random

    return f"R{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"


@router.get("", response_model=WalletOut, summary="查询余额")
async def get_wallet(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    wallet = await db.scalar(select(Wallet).where(Wallet.user_id == user.id))
    if wallet is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "钱包不存在")
    return wallet


@router.post("/recharge", response_model=RechargeOut, summary="充值（1元 = 10书币，mock 支付）")
async def recharge(
    data: RechargeIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    coins = data.amount * 10  # 汇率 1:10
    order = RechargeOrder(
        order_no=_gen_order_no(),
        user_id=user.id,
        amount=data.amount,
        coins=coins,
        payment_method=data.payment_method,
        status="success",  # mock：直接成功
        paid_at=datetime.now(timezone.utc),
    )
    db.add(order)

    # 加余额（UPSERT：钱包不存在则创建）
    wallet = await db.scalar(select(Wallet).where(Wallet.user_id == user.id))
    if wallet is None:
        wallet = Wallet(user_id=user.id, balance=0)
        db.add(wallet)
    wallet.balance = float(wallet.balance) + coins
    wallet.total_recharged = float(wallet.total_recharged) + coins

    await db.commit()
    return RechargeOut(
        order_no=order.order_no,
        amount=float(order.amount),
        coins=float(order.coins),
        status=order.status,
        balance_after=float(wallet.balance),
    )
