"""Add drafts, hashtags and draft_hashtags tables

Revision ID: d4e5f6a7b8c9
Revises: b2e7f3a1c4d5
Create Date: 2026-02-09 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "b2e7f3a1c4d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "drafts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], onupdate="CASCADE", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "hashtags",
        sa.Column("text", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("text"),
    )
    op.create_table(
        "draft_hashtags",
        sa.Column("draft_id", sa.Uuid(), nullable=False),
        sa.Column("hashtag_text", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["draft_id"], ["drafts.id"], onupdate="CASCADE", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["hashtag_text"], ["hashtags.text"], onupdate="CASCADE", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("draft_id", "hashtag_text"),
    )


def downgrade() -> None:
    op.drop_table("draft_hashtags")
    op.drop_table("hashtags")
    op.drop_table("drafts")
