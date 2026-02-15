"""Add file_id foreign key to drafts

Revision ID: f1a2b3c4d5e6
Revises: e5f6a7b8c9d0
Create Date: 2026-02-15 00:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("drafts", sa.Column("file_id", sa.Uuid(), nullable=True))
    op.create_index("ix_drafts_file_id", "drafts", ["file_id"], unique=False)
    op.create_foreign_key(
        "fk_drafts_file_id_s3_files",
        "drafts",
        "s3_files",
        ["file_id"],
        ["id"],
        onupdate="CASCADE",
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_drafts_file_id_s3_files", "drafts", type_="foreignkey")
    op.drop_index("ix_drafts_file_id", table_name="drafts")
    op.drop_column("drafts", "file_id")
