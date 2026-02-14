from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, Uuid, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from brain.infrastructure.db.models.base import Base


class ApiKeyDB(Base):
    __tablename__ = "api_keys"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(length=255), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(length=64), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
