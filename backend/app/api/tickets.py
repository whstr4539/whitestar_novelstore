"""月票/推荐票接口：投票（防重复）+ 月票榜（Redis ZSET 实时排行 + PG 持久化）"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models import Novel, Ticket, User
from app.redis_client import get_redis
from app.schemas import IdParam, TicketIn, TicketOut, TicketRankItem
from app.services.cache import cache_key, delete_keys

router = APIRouter(prefix="/api", tags=["月票"])

TICKET_RANK_KEY = "rank:tickets"  # Redis ZSET：小说ID -> 票数


@router.post("/novels/{novel_id}/tickets", response_model=TicketOut, summary="投票（月票/推荐票，每人每书每类一票）")
async def vote_ticket(
    novel_id: IdParam,
    data: TicketIn,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    user: User = Depends(get_current_user),
):
    novel = await db.get(Novel, novel_id)
    if novel is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "小说不存在")

    # 防重复：应用层先查快速返回，并发由唯一约束 uq_tickets_user_novel_type 兜底
    exists = await db.scalar(
        select(Ticket.id).where(
            Ticket.user_id == user.id,
            Ticket.novel_id == novel_id,
            Ticket.ticket_type == data.ticket_type,
        )
    )
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, f"你已投过{data.ticket_type}票")

    db.add(Ticket(user_id=user.id, novel_id=novel_id, ticket_type=data.ticket_type))
    novel.total_tickets += 1
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, f"你已投过{data.ticket_type}票（并发重复请求被拦截）")

    # 投票成功后再更新热榜与缓存（Redis 故障不阻塞主流程）
    try:
        await redis.zincrby(TICKET_RANK_KEY, 1, str(novel_id))
        await delete_keys(redis, cache_key("novel", novel_id))
    except Exception:  # noqa: BLE001
        pass

    return TicketOut(
        novel_id=novel_id,
        novel_title=novel.title,
        ticket_type=data.ticket_type,
        total_tickets=novel.total_tickets,
    )


@router.get("/novels/tickets/rank", response_model=list[TicketRankItem], summary="月票排行榜（Redis ZSET 实时排名）")
async def ticket_rank(
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    raw = await redis.zrevrange(TICKET_RANK_KEY, 0, limit - 1, withscores=True)

    # 自愈：ZSET 为空（Redis 重建/重置）时从 PG 聚合回填
    if not raw:
        rows = (
            await db.execute(
                select(Ticket.novel_id, func.count(Ticket.id))
                .group_by(Ticket.novel_id)
            )
        ).all()
        if rows:
            # 排除已下架作品
            active_ids = set(
                (await db.scalars(select(Novel.id).where(Novel.status != "banned"))).all()
            )
            pipeline = redis.pipeline()
            for nid, cnt in rows:
                if int(nid) in active_ids and cnt > 0:
                    pipeline.zadd(TICKET_RANK_KEY, {str(nid): int(cnt)})
            await pipeline.execute()
            raw = await redis.zrevrange(TICKET_RANK_KEY, 0, limit - 1, withscores=True)

    if not raw:
        return []

    ids = [int(nid) for nid, _ in raw]
    titles = {
        n.id: n.title
        for n in (
            await db.scalars(select(Novel).where(Novel.id.in_(ids)))
        ).all()
    }
    return [
        TicketRankItem(
            rank=i + 1,
            novel_id=int(nid),
            title=titles.get(int(nid), "未知"),
            ticket_count=int(score),
        )
        for i, (nid, score) in enumerate(raw)
    ]
