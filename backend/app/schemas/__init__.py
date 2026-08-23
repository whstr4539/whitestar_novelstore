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


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nickname: str
    avatar: str | None = None
    email: str | None = None
    role: str
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


class BookshelfOut(BaseModel):
    items: list[BookshelfItem]


# ---------- 钱包 ----------
class WalletOut(BaseModel):
    user_id: int
    balance: float
    total_recharged: float
    updated_at: datetime


class RechargeIn(BaseModel):
    amount: float = Field(gt=0, le=10000, description="充值金额（元）")
    payment_method: Literal["alipay", "wechat", "mock"] = "mock"


class RechargeOut(BaseModel):
    order_no: str
    amount: float
    coins: float
    status: str
    balance_after: float | None = None


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
    is_vip: bool = False


class ChapterCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, description="章节正文")
    price: float = Field(default=0, ge=0, description="书币价格，0=免费")
    is_vip: bool = False
    is_free: bool = False


class ChapterUpdateIn(BaseModel):
    title: str | None = None
    content: str | None = None
    price: float | None = Field(default=None, ge=0)
    is_vip: bool | None = None
    is_free: bool | None = None


class ChapterCreatedOut(BaseModel):
    id: int
    novel_id: int
    chapter_no: int
    title: str
    word_count: int
    novel_chapter_count: int
    novel_word_count: int


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
