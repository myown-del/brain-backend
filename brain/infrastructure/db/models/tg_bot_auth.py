from datetime import datetime

from uuid import UUID

from sqlalchemy import DateTime, Integer, String, Uuid, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from brain.infrastructure.db.models.base import Base


class TelegramBotAuthSessionDB(Base):
    __tablename__ = "tg_bot_auth"

    id: Mapped[str] = mapped_column(String(length=16), primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    jwt_token_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("jwt_refresh_tokens.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
