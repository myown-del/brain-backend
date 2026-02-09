from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from brain.infrastructure.db.models.base import Base
from brain.infrastructure.db.models.mixins import utcnow_wrapper


class HashtagDB(Base):
    __tablename__ = "hashtags"

    text: Mapped[str] = mapped_column(String(length=255), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utcnow_wrapper,
        server_default=func.now(),
    )

    drafts = relationship(
        "DraftDB",
        secondary="draft_hashtags",
        back_populates="hashtags",
        lazy="selectin",
        overlaps="draft_hashtags",
    )
    draft_hashtags = relationship(
        "DraftHashtagDB",
        back_populates="hashtag",
        cascade="all, delete-orphan",
    )


class DraftHashtagDB(Base):
    __tablename__ = "draft_hashtags"
    __mapper_args__ = {"confirm_deleted_rows": False}

    draft_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("drafts.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    hashtag_text: Mapped[str] = mapped_column(
        String(length=255),
        ForeignKey("hashtags.text", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )

    draft = relationship(
        "DraftDB",
        back_populates="draft_hashtags",
        lazy="selectin",
        overlaps="drafts",
    )
    hashtag = relationship(
        "HashtagDB",
        back_populates="draft_hashtags",
        lazy="selectin",
        overlaps="drafts",
    )
