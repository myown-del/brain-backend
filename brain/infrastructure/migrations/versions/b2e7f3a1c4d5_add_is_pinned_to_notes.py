"""Add is_pinned to notes

Revision ID: b2e7f3a1c4d5
Revises: a1d2c3e4f5a6
Create Date: 2026-02-08 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b2e7f3a1c4d5"
down_revision: Union[str, None] = "a1d2c3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "notes",
        sa.Column("is_pinned", sa.Boolean(), server_default=sa.false(), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("notes", "is_pinned")
