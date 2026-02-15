from uuid import UUID

from datetime import datetime

from sqlalchemy import DateTime, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from brain.domain.time import utc_now
from brain.infrastructure.db.models.base import Base


class S3FileDB(Base):
    __tablename__ = "s3_files"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(String(length=256), nullable=False)
    path: Mapped[str] = mapped_column(String(length=256), nullable=False)
    content_type: Mapped[str] = mapped_column(String(length=64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )
