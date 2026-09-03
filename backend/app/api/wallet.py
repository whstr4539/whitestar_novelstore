"""钱包接口：余额 / 充值（模拟真实支付四步：下单 → 收银台受理 → 渠道回调 → 前端轮询终态）"""
import asyncio
import hashlib
import hmac
import logging
import random
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import async_session, get_db
from app.models import Chapter, ChapterPurchase, Novel, RechargeOrder, Reward, User, Wallet
from app.schemas import BillsOut, NotifyIn, OrderOut, PayIn, PayOut, RechargeIn, RechargeOut, WalletOut

logger = logging.getLogger("uvicorn.error")
router = APIRouter(prefix="/api/wallet", tags=["钱包"])

# 模拟支付参数
PAY_DELAY_SECONDS = 3                 # 模拟渠道处理耗时（秒）
SUCCESS_RATE = 0.8                    # 渠道成功率（模拟风控）
ORDER_TIMEOUT = timedelta(minutes=15) # 未支付自动关单
MOCK_PAY_PREFIX = "https://pay.alipay-mock.com/cashier/"
MOCK_SIGN_KEY = "mock-channel-sign-key-2024"  # 真实场景为渠道分发的商户密钥


def _gen_order_no() -> str:
    """生成业务订单号：R + 时间戳 + UUID 片段（并发下单不碰撞）"""
    return f"R{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8]}"


def _mock_pay_url(order_no: str) -> str:
    """模拟第三方收银台地址（仅演示，无真实跳转）"""
    return f"{MOCK_PAY_PREFIX}{order_no}"


def _sign(order_no: str, result: str) -> str:
    """模拟渠道签名：md5(订单号 + 结果 + 密钥)（真实为 RSA/HMAC 验签）"""
    return hashlib.md5(f"{order_no}{result}{MOCK_SIGN_KEY}".encode()).hexdigest()


def _verify_sign(order_no: str, result: str, sign: str) -> bool:
    """验签：防止伪造回调（compare_digest 防时序攻击）"""
    return hmac.compare_digest(_sign(order_no, result), sign)


async def _process_callback(order_no: str, result: str) -> None:
    """回调核心逻辑（独立开会话，供渠道模拟任务与 notify 接口共用）：
    行锁订单 → 幂等 → 状态机 → 成功才入账 → 同一事务提交"""
    async with async_session() as db:
        # 行锁：并发重复回调串行化
        order = await db.scalar(
            select(RechargeOrder).where(RechargeOrder.order_no == order_no).with_for_update()
        )
        if order is None:
            return

        # 幂等：已终结订单直接忽略，防重复入账
        if order.status != "pending":
            return

        # 超时关单
        if order.created_at and datetime.now(timezone.utc) - order.created_at > ORDER_TIMEOUT:
            order.status = "failed"
            await db.commit()
            return

        if result == "fail":
            order.status = "failed"
            await db.commit()
            return

        if result == "cancel":
            order.status = "cancelled"
            await db.commit()
            return

        # 成功：订单 + 钱包同事务入账
        order.status = "success"
        order.paid_at = datetime.now(timezone.utc)

        wallet = await db.scalar(
            select(Wallet).where(Wallet.user_id == order.user_id).with_for_update()
        )
        if wallet is None:
            wallet = Wallet(user_id=order.user_id, balance=0, total_recharged=0)
            db.add(wallet)
        wallet.balance = float(wallet.balance) + float(order.coins)
        wallet.total_recharged = float(wallet.total_recharged) + float(order.coins)

        await db.commit()


async def _simulate_channel(order_no: str) -> None:
    """后台任务扮演第三方渠道：等待数秒后携带结果回调商户 notify"""
    await asyncio.sleep(PAY_DELAY_SECONDS)
    # 结果由渠道内部决定（风控等），商户不可预知
    result = "success" if random.random() < SUCCESS_RATE else "fail"
    await _process_callback(order_no, result)


@router.get("", response_model=WalletOut, summary="查询余额")
async def get_wallet(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    wallet = await db.scalar(select(Wallet).where(Wallet.user_id == user.id))
    if wallet is None:
        wallet = Wallet(user_id=user.id, balance=0, total_recharged=0)
        db.add(wallet)
        await db.commit()
        await db.refresh(wallet)
    return wallet


@router.post("/recharge", response_model=RechargeOut, status_code=201,
             summary="创建充值订单（1元 = 10书币，下单后跳转模拟收银台）")
async def recharge(data: RechargeIn, db: AsyncSession = Depends(get_db),
                   user: User = Depends(get_current_user)):
    """第一步：只创建待支付订单，不动钱包余额；支付结果由渠道回调确认后入账"""
    coins = data.amount * 10
    order = RechargeOrder(
        order_no=_gen_order_no(), user_id=user.id, amount=data.amount,
        coins=coins, payment_method=data.payment_method, status="pending",
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return RechargeOut(
        order_no=order.order_no, amount=float(order.amount), coins=float(order.coins),
        status=order.status, payment_method=order.payment_method,
        pay_url=_mock_pay_url(order.order_no),
    )


@router.post("/pay/notify", summary="模拟第三方支付渠道回调（notify_url）")
async def pay_notify(data: NotifyIn):
    """渠道回调入口：验签防伪造 → 幂等入账 → 应答 success（非 success 渠道会重试）"""
    if not _verify_sign(data.order_no, data.result, data.sign):
        logger.warning("支付回调验签失败: order=%s result=%s", data.order_no, data.result)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "签名校验失败")

    await _process_callback(data.order_no, data.result)
    return {"code": "success"}


@router.post("/pay/{order_no}", response_model=PayOut, summary="模拟渠道收银台（受理支付，立即返回，回调稍后到达）")
async def pay_order(order_no: str, data: PayIn, background_tasks: BackgroundTasks,
                    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """第二步：商户把订单提交给渠道。渠道受理后立即返回「处理中」，
    支付结果由后台任务模拟渠道在 3 秒后回调 /pay/notify（前端轮询订单状态）。"""
    # 行锁：并发受理同一订单/与回调结算串行化，避免状态被并发覆盖
    order = await db.scalar(
        select(RechargeOrder).where(RechargeOrder.order_no == order_no).with_for_update()
    )
    if order is None or order.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "充值订单不存在")
    if order.status != "pending":
        # 已处理：幂等返回历史状态
        return PayOut(order_no=order_no, status=order.status,
                      amount=float(order.amount), coins=float(order.coins),
                      balance_after=None)

    # 渠道过期关单
    if order.created_at and datetime.now(timezone.utc) - order.created_at > ORDER_TIMEOUT:
        order.status = "failed"
        await db.commit()
        raise HTTPException(status.HTTP_410_GONE, "订单已超时关闭")

    # 必须先提交释放行锁再调度后台任务：BackgroundTasks 在依赖清理（session.close）
    # 之前执行，若仍持有 FOR UPDATE 行锁，回调开新会话会永久等锁（死锁）。
    await db.commit()

    background_tasks.add_task(_simulate_channel, order_no)

    return PayOut(order_no=order_no, status="processing",
                  amount=float(order.amount), coins=float(order.coins),
                  balance_after=None)


@router.post("/pay/{order_no}/cancel", response_model=PayOut, summary="取消支付（即时关单，不走渠道）")
async def cancel_order(order_no: str, db: AsyncSession = Depends(get_db),
                       user: User = Depends(get_current_user)):
    """用户主动取消（收银台点取消）：即时关单，不经过渠道（真实场景为直接关闭支付宝订单）"""
    # 行锁：与异步回调 _process_callback 的 FOR UPDATE 串行化，避免"已入账却显示取消"的竞态
    order = await db.scalar(
        select(RechargeOrder).where(RechargeOrder.order_no == order_no).with_for_update()
    )
    if order is None or order.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "充值订单不存在")
    if order.status == "pending":
        order.status = "cancelled"
        await db.commit()
    return PayOut(order_no=order_no, status=order.status,
                  amount=float(order.amount), coins=float(order.coins),
                  balance_after=None)


@router.get("/order/{order_no}", response_model=OrderOut, summary="订单状态查询（前端轮询）")
async def order_status(order_no: str, db: AsyncSession = Depends(get_db),
                       user: User = Depends(get_current_user)):
    """前端在收银台轮询此接口获取终态（success/failed/cancelled）"""
    order = await db.scalar(select(RechargeOrder).where(RechargeOrder.order_no == order_no))
    if order is None or order.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "充值订单不存在")
    # 终态时回填钱包余额：回调与入账在同一事务提交，读到 success 即入账已完成
    balance_after = None
    if order.status != "pending":
        wallet = await db.scalar(select(Wallet).where(Wallet.user_id == user.id))
        balance_after = float(wallet.balance) if wallet else 0.0
    return OrderOut(order_no=order.order_no, status=order.status,
                    amount=float(order.amount), coins=float(order.coins),
                    balance_after=balance_after)


@router.get("/bills", response_model=BillsOut, summary="账单流水（充值/订阅/打赏，统一格式）")
async def my_bills(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """个人账单：三条资金流水合并为统一格式，按时间倒序"""
    # 充值（只取成功订单）
    rows = await db.execute(
        select(RechargeOrder)
        .where(RechargeOrder.user_id == user.id, RechargeOrder.status == "success")
        .order_by(RechargeOrder.paid_at.desc())
    )
    items = [
        {
            "type": "recharge",
            "title": f"充值 {o.amount} 元",
            "detail": f"订单 {o.order_no} · {o.payment_method}",
            "amount": float(o.coins),
            "direction": "in",
            "created_at": o.paid_at or o.created_at,
        }
        for o in rows.scalars().all()
    ]

    # 章节订阅
    rows = await db.execute(
        select(ChapterPurchase, Chapter.chapter_no, Chapter.title, Novel.title)
        .join(Chapter, Chapter.id == ChapterPurchase.chapter_id)
        .join(Novel, Novel.id == Chapter.novel_id)
        .where(ChapterPurchase.user_id == user.id)
        .order_by(ChapterPurchase.purchased_at.desc())
    )
    items += [
        {
            "type": "purchase",
            "title": f"订阅《{novel_title}》第{no}章",
            "detail": chapter_title,
            "amount": float(p.price_paid),
            "direction": "out",
            "created_at": p.purchased_at,
        }
        for p, no, chapter_title, novel_title in rows.all()
    ]

    # 打赏
    rows = await db.execute(
        select(Reward, Novel.title)
        .join(Novel, Novel.id == Reward.novel_id)
        .where(Reward.user_id == user.id)
        .order_by(Reward.created_at.desc())
    )
    items += [
        {
            "type": "reward",
            "title": f"打赏《{novel_title}》",
            "detail": r.message or None,
            "amount": float(r.amount),
            "direction": "out",
            "created_at": r.created_at,
        }
        for r, novel_title in rows.all()
    ]

    items.sort(key=lambda x: x["created_at"], reverse=True)
    total_in = sum(i["amount"] for i in items if i["direction"] == "in")
    total_out = sum(i["amount"] for i in items if i["direction"] == "out")
    return BillsOut(items=items, total_in=total_in, total_out=total_out)
