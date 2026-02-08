from __future__ import annotations

from uuid import UUID

from sqlalchemy import Uuid, String, Text, Column, ForeignKey, UniqueConstraint, JSON, Boolean
from sqlalchemy.orm import mapped_column, Mapped, relationship

from brain.infrastructure.db.models.base import Base
from brain.infrastructure.db.models.mixins import CreatedUpdatedMixin


class NoteDB(Base, CreatedUpdatedMixin):
    __tablename__ = "notes"
    __table_args__ = (UniqueConstraint("user_id", "title", name="uq_notes_user_id_title"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(length=255), nullable=False)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    represents_keyword_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("keywords.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    link_intervals: Mapped[list[list[int]]] = mapped_column(JSON, default=list, nullable=False)

    user = relationship("UserDB", back_populates="notes", lazy="selectin")
    note_keywords = relationship(
        "NoteKeywordDB",
        back_populates="note",
        cascade="all, delete-orphan",
        overlaps="notes",
    )
    keywords = relationship(
        "KeywordDB",
        secondary="note_keywords",
        back_populates="notes",
        lazy="selectin",
        overlaps="note_keywords,note,keyword",
    )
