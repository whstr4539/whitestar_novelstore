"""章节域模型：chapters / chapter_contents / chapter_purchases"""
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Chapter(Base):
    __tablename__ = "chapters"
    __table_args__ = (UniqueConstraint("novel_id", "chapter_no", name="uq_chapters_novel_no"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    novel_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("novels.id", ondelete="CASCADE"), index=True
    )
    chapter_no: Mapped[int] = mapped_column()
    title: Mapped[str] = mapped_column(String(200))
    price: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    is_vip: Mapped[bool] = mapped_column(Boolean, default=False)
    is_free: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    word_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    novel: Mapped["Novel"] = relationship(back_populates="chapters")  # type: ignore[name-defined]
    content: Mapped["ChapterContent | None"] = relationship(back_populates="chapter", uselist=False)


class ChapterContent(Base):
    """章节正文（1:1 拆分）"""

    __tablename__ = "chapter_contents"

    chapter_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("chapters.id", ondelete="CASCADE"), primary_key=True
    )
    content: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    chapter: Mapped["Chapter"] = relationship(back_populates="content")


class ChapterPurchase(Base):
    """章节订阅记录（核心：VIP 章购买凭证）"""

    __tablename__ = "chapter_purchases"
    __table_args__ = (UniqueConstraint("user_id", "chapter_id", name="uq_purchases_user_chapter"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    chapter_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("chapters.id"))
    price_paid: Mapped[float] = mapped_column(Numeric(10, 2))
    purchased_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
