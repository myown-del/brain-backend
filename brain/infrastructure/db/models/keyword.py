from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from brain.infrastructure.db.models.base import Base
from brain.infrastructure.db.models.mixins import CreatedUpdatedMixin


class KeywordDB(Base, CreatedUpdatedMixin):
    __tablename__ = "keywords"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_keywords_user_id_name"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(length=255), nullable=False)

    user = relationship("UserDB", back_populates="keywords", lazy="selectin")
    note_keywords = relationship(
        "NoteKeywordDB",
        back_populates="keyword",
        cascade="all, delete-orphan",
    )
    notes = relationship(
        "NoteDB",
        secondary="note_keywords",
        back_populates="keywords",
        lazy="selectin",
        overlaps="note_keywords",
    )


class NoteKeywordDB(Base):
    __tablename__ = "note_keywords"
    __mapper_args__ = {"confirm_deleted_rows": False}

    note_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("notes.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    keyword_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("keywords.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )

    note = relationship("NoteDB", back_populates="note_keywords", lazy="selectin", overlaps="notes")
    keyword = relationship("KeywordDB", back_populates="note_keywords", lazy="selectin", overlaps="notes")
