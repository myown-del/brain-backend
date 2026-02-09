from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from brain.infrastructure.db.models.base import Base
from brain.infrastructure.db.models.mixins import CreatedUpdatedMixin


class DraftDB(Base, CreatedUpdatedMixin):
    __tablename__ = "drafts"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    text: Mapped[str | None] = mapped_column(Text, nullable=True)

    user = relationship("UserDB", back_populates="drafts", lazy="selectin")
    draft_hashtags = relationship(
        "DraftHashtagDB",
        back_populates="draft",
        cascade="all, delete-orphan",
        overlaps="hashtags",
    )
    hashtags = relationship(
        "HashtagDB",
        secondary="draft_hashtags",
        back_populates="drafts",
        lazy="selectin",
        overlaps="draft_hashtags,draft,hashtag",
    )
