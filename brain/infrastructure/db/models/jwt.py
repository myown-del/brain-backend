from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, Uuid, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from brain.infrastructure.db.models.base import Base


class JwtRefreshTokenDB(Base):
    __tablename__ = "jwt_refresh_tokens"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    token: Mapped[str] = mapped_column(String(length=1024), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
