"""ORM 模型统一出口"""
from app.models.chapter import Chapter, ChapterContent, ChapterPurchase
from app.models.interaction import (
    Comment,
    Favorite,
    Notice,
    NovelReview,
    ReadingHistory,
    Reward,
    Ticket,
)
from app.models.novel import Category, Novel, NovelCategory
from app.models.user import RechargeOrder, User, Wallet

__all__ = [
    "User",
    "Wallet",
    "RechargeOrder",
    "Category",
    "Novel",
    "NovelCategory",
    "Chapter",
    "ChapterContent",
    "ChapterPurchase",
    "Favorite",
    "ReadingHistory",
    "Comment",
    "Ticket",
    "Reward",
    "NovelReview",
    "Notice",
]
