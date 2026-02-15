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
    file_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("s3_files.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    text: Mapped[str | None] = mapped_column(Text, nullable=True)

    user = relationship("UserDB", back_populates="drafts", lazy="selectin")
    file = relationship(
        "S3FileDB",
        lazy="selectin",
        uselist=False,
        foreign_keys="DraftDB.file_id",
    )
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
