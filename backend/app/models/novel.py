"""作品域模型：categories / novels / novel_category"""
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(30), unique=True)
    parent_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("categories.id"), nullable=True
    )


class Novel(Base):
    __tablename__ = "novels"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    author_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(100), index=True)
    intro: Mapped[str | None] = mapped_column(Text)
    cover_url: Mapped[str | None] = mapped_column(String(255))
    category_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("categories.id"))
    status: Mapped[str] = mapped_column(String(12), default="serializing")
    word_count: Mapped[int] = mapped_column(BigInteger, default=0)
    chapter_count: Mapped[int] = mapped_column(default=0)
    total_views: Mapped[int] = mapped_column(BigInteger, default=0)
    total_favorites: Mapped[int] = mapped_column(BigInteger, default=0)
    total_tickets: Mapped[int] = mapped_column(BigInteger, default=0)
    score: Mapped[float] = mapped_column(Numeric(3, 1), default=0)
    is_vip: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    author: Mapped["User"] = relationship()  # type: ignore[name-defined]
    category: Mapped["Category | None"] = relationship()
    chapters: Mapped[list["Chapter"]] = relationship(back_populates="novel")  # type: ignore[name-defined]


class NovelCategory(Base):
    """小说-分类多对多中间表"""

    __tablename__ = "novel_category"

    novel_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("novels.id", ondelete="CASCADE"), primary_key=True
    )
    category_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True
    )
