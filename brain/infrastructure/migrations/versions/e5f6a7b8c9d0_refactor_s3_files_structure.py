"""Refactor s3_files structure to name/path/content_type

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-02-15 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("s3_files", sa.Column("path", sa.String(length=256), nullable=True))

    op.execute("UPDATE s3_files SET path = object_name WHERE path IS NULL")
    op.execute("UPDATE s3_files SET content_type = 'application/octet-stream' WHERE content_type IS NULL")

    op.alter_column(
        "s3_files",
        "object_name",
        new_column_name="name",
        type_=sa.String(length=256),
        existing_type=sa.String(length=255),
        existing_nullable=False,
    )

    op.execute("UPDATE s3_files SET name = regexp_replace(path, '^.*/', '')")

    op.alter_column(
        "s3_files",
        "path",
        existing_type=sa.String(length=256),
        nullable=False,
    )
    op.alter_column(
        "s3_files",
        "content_type",
        type_=sa.String(length=64),
        existing_type=sa.String(length=255),
        nullable=False,
    )
    op.drop_column("s3_files", "updated_at")


def downgrade() -> None:
    op.add_column(
        "s3_files",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.alter_column(
        "s3_files",
        "content_type",
        type_=sa.String(length=255),
        existing_type=sa.String(length=64),
        nullable=True,
    )
    op.alter_column(
        "s3_files",
        "name",
        new_column_name="object_name",
        type_=sa.String(length=255),
        existing_type=sa.String(length=256),
        existing_nullable=False,
    )
    op.drop_column("s3_files", "path")
