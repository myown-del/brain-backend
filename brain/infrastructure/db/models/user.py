from uuid import UUID

from sqlalchemy import Uuid, Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from brain.infrastructure.db.models.base import Base
from brain.infrastructure.db.models.mixins import CreatedUpdatedMixin
from brain.infrastructure.db.models.s3 import S3FileDB


class UserDB(Base, CreatedUpdatedMixin):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True)
    username: Mapped[str | None] = mapped_column(String, nullable=True)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str | None] = mapped_column(String, nullable=True)
    profile_picture_file_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("s3_files.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )

    notes = relationship("NoteDB", back_populates="user", lazy="selectin")
    drafts = relationship("DraftDB", back_populates="user", lazy="selectin")
    keywords = relationship("KeywordDB", back_populates="user", lazy="selectin")
    profile_picture_file = relationship(
        S3FileDB,
        lazy="selectin",
        uselist=False,
        foreign_keys="UserDB.profile_picture_file_id",
    )
