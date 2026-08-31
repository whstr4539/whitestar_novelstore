"""互动域模型：favorites / reading_history / comments / tickets / rewards / novel_reviews / notices"""
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Favorite(Base):
    """书架"""

    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "novel_id", name="uq_favorites_user_novel"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    novel_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("novels.id", ondelete="CASCADE"))
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReadingHistory(Base):
    """阅读记录（每本书每用户一条）"""

    __tablename__ = "reading_history"
    __table_args__ = (UniqueConstraint("user_id", "novel_id", name="uq_history_user_novel"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    novel_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("novels.id", ondelete="CASCADE"))
    chapter_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("chapters.id"))
    progress: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    last_read_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Comment(Base):
    """评论：本章说 / 书评 / 楼中楼"""

    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    novel_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("novels.id", ondelete="CASCADE"), index=True)
    chapter_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("chapters.id", ondelete="CASCADE"))
    parent_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("comments.id", ondelete="CASCADE"))
    paragraph_pos: Mapped[int | None] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(String(500))
    likes: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship()  # type: ignore[name-defined]


class CommentLike(Base):
    """评论点赞记录：唯一约束保证每人每评论一赞（可取消）"""

    __tablename__ = "comment_likes"
    __table_args__ = (UniqueConstraint("comment_id", "user_id", name="uq_comment_likes"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    comment_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("comments.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Ticket(Base):
    """月票/推荐票（每人每书每类一票，唯一约束防并发重复）"""

    __tablename__ = "tickets"
    __table_args__ = (
        UniqueConstraint("user_id", "novel_id", "ticket_type", name="uq_tickets_user_novel_type"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    novel_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("novels.id"), index=True)
    ticket_type: Mapped[str] = mapped_column(String(10), default="monthly")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship()  # type: ignore[name-defined]


class Reward(Base):
    """打赏"""

    __tablename__ = "rewards"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    novel_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("novels.id"))
    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    message: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship()  # type: ignore[name-defined]


class NovelReview(Base):
    """书评评分"""

    __tablename__ = "novel_reviews"
    __table_args__ = (UniqueConstraint("user_id", "novel_id", name="uq_reviews_user_novel"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    novel_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("novels.id"))
    rating: Mapped[int] = mapped_column(SmallInteger)
    content: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship()  # type: ignore[name-defined]


class Notice(Base):
    """公告"""

    __tablename__ = "notices"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
