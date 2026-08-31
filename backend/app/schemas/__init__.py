"""Pydantic 请求/响应模型"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# ---------- 通用 ----------
class Message(BaseModel):
    detail: str


class Page(BaseModel):
    total: int
    page: int
    page_size: int


# ---------- 用户 ----------
class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=50, description="登录名")
    password: str = Field(min_length=6, max_length=64, description="密码")
    nickname: str = Field(min_length=1, max_length=50, description="昵称")
    email: str | None = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserUpdateIn(BaseModel):
    """编辑个人资料"""

    nickname: str | None = Field(default=None, min_length=1, max_length=50)
    email: str | None = Field(default=None, max_length=100)
    avatar: str | None = Field(default=None, max_length=255)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nickname: str
    avatar: str | None = None
    email: str | None = None
    role: str
    status: int = 1  # 1正常 0封禁（管理后台需要）
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- 小说 ----------
class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    parent_id: int | None = None


class NovelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    intro: str | None = None
    cover_url: str | None = None
    status: str
    word_count: int
    chapter_count: int
    total_views: int
    total_favorites: int
    total_tickets: int
    score: float
    is_vip: bool
    created_at: datetime
    category_id: int | None = None  # 主分类ID（前端按分类生成封面配色）
    category: CategoryOut | None = None
    author: UserOut | None = None


class NovelListOut(BaseModel):
    items: list[NovelOut]
    total: int


# ---------- 章节 ----------
class ChapterMetaOut(BaseModel):
    """章节元信息（目录用，不含正文）"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    chapter_no: int
    title: str
    price: float
    is_vip: bool
    is_free: bool
    word_count: int
    created_at: datetime


class ChapterReadOut(BaseModel):
    """阅读返回：正文 + 元信息 + 是否已购"""

    chapter: ChapterMetaOut
    content: str
    purchased: bool
    novel_title: str | None = None
    novel_id: int | None = None


class PurchaseOut(BaseModel):
    chapter_id: int
    price_paid: float
    balance_after: float
    purchased_at: datetime


# ---------- 书架 ----------
class BookshelfItem(BaseModel):
    novel: NovelOut
    added_at: datetime
    chapter_id: int | None = None  # 阅读历史条目的最近阅读章节（书架条目为 None）


class BookshelfOut(BaseModel):
    items: list[BookshelfItem]


# ---------- 钱包 ----------
class WalletOut(BaseModel):
    user_id: int
    balance: float
    total_recharged: float
    updated_at: datetime


class RechargeOut(BaseModel):
    """创建充值订单响应：订单待支付，余额未变"""

    order_no: str
    amount: float
    coins: float
    status: str  # pending
    payment_method: str = "mock"
    pay_url: str | None = None  # 模拟第三方收银台地址


class PayIn(BaseModel):
    """模拟支付受理入参：无 result（结果由渠道回调决定，不由商户指定）"""

    pass


class NotifyIn(BaseModel):
    """模拟渠道回调入参：订单号 + 结果 + 签名（验签防伪造）"""

    order_no: str
    result: Literal["success", "fail", "cancel"]
    sign: str


class OrderOut(BaseModel):
    """订单状态查询（前端轮询用）"""

    order_no: str
    status: str
    amount: float
    coins: float
    balance_after: float | None = None


class BillItem(BaseModel):
    """账单流水条目（充值/订阅/打赏统一格式）"""

    type: Literal["recharge", "purchase", "reward"]
    title: str
    detail: str | None = None
    amount: float  # 正数，方向由 direction 表示
    direction: Literal["in", "out"]
    created_at: datetime


class BillsOut(BaseModel):
    """账单响应：流水 + 累计收入/支出"""

    items: list[BillItem]
    total_in: float
    total_out: float


class RechargeIn(BaseModel):
    amount: float = Field(gt=0, le=10000, description="充值金额（元）")
    payment_method: Literal["alipay", "wechat", "mock"] = "mock"


class PayOut(BaseModel):
    """支付确认响应：status 为 success / failed / cancelled / pending"""

    order_no: str
    status: str
    amount: float
    coins: float
    balance_after: float | None = None  # 仅成功时返回新余额


# ---------- 评论 ----------
class CommentIn(BaseModel):
    content: str = Field(min_length=1, max_length=500)
    chapter_id: int | None = None
    parent_id: int | None = None


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    novel_id: int
    chapter_id: int | None = None
    parent_id: int | None = None
    content: str
    likes: int
    created_at: datetime
    user: UserOut | None = None
    novel_title: str | None = None
    chapter_title: str | None = None
    liked: bool = False  # 当前用户是否已赞（未登录恒为 False）


class CommentLikeOut(BaseModel):
    liked: bool
    likes: int


class ReviewIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    content: str | None = Field(default=None, max_length=1000)


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    novel_id: int
    rating: int
    content: str | None = None
    created_at: datetime
    user: UserOut | None = None


# ---------- 月票 ----------
class TicketIn(BaseModel):
    ticket_type: Literal["monthly", "recommend"] = "monthly"


class TicketOut(BaseModel):
    novel_id: int
    novel_title: str | None = None
    ticket_type: str
    total_tickets: int


class TicketRankItem(BaseModel):
    rank: int
    novel_id: int
    title: str
    ticket_count: int


# ---------- 打赏 ----------
class RewardIn(BaseModel):
    amount: float = Field(gt=0, le=10000, description="打赏书币数")
    message: str | None = Field(default=None, max_length=200)


class RewardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    novel_id: int
    amount: float
    message: str | None = None
    created_at: datetime
    user: UserOut | None = None


# ---------- 作者后台 ----------
class AuthorNovelIn(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    intro: str | None = Field(default=None, max_length=2000)
    cover_url: str | None = None
    category_id: int | None = None


class ChapterCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, description="章节正文")
    price: float = Field(default=0, ge=0, description="书币价格，0=免费")
    is_free: bool = False


class ChapterUpdateIn(BaseModel):
    title: str | None = None
    content: str | None = None
    price: float | None = Field(default=None, ge=0)
    is_free: bool | None = None


class ChapterCreatedOut(BaseModel):
    id: int
    novel_id: int
    chapter_no: int
    title: str
    word_count: int
    novel_chapter_count: int
    novel_word_count: int


class AuthorStatsOut(BaseModel):
    """写作台概览：作品数 / 点击 / 章节 / 收入"""

    novel_count: int
    total_views: int
    chapter_count: int
    word_count: int
    chapter_revenue: float
    reward_revenue: float
    total_revenue: float
    purchase_count: int
    reward_count: int


# ---------- 公告 ----------
class NoticeIn(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)


class NoticeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    is_active: bool
    created_at: datetime


# ---------- 阅读进度 ----------
class ProgressIn(BaseModel):
    novel_id: int
    chapter_id: int
    progress: float = Field(ge=0, le=100)
