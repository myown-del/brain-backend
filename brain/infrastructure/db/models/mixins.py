from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


from datetime import datetime
from brain.domain.time import utc_now


def utcnow_wrapper() -> datetime:
    """
    Решает баг в adaptix
    """
    return utc_now()


class CreatedUpdatedMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow_wrapper,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow_wrapper,
        server_default=func.now(),
    )
