"""add_sticker_packs_table

Revision ID: 8d4c1b2a9e73
Revises: 5f6c7a8b9d10
Create Date: 2026-02-17 20:10:00.000000

"""

from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence


# revision identifiers, used by Alembic.
revision: str = "8d4c1b2a9e73"
down_revision: str | Sequence[str] | None = "5f6c7a8b9d10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    return table_name in inspect(bind).get_table_names()


def _index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    return index_name in {index["name"] for index in inspect(bind).get_indexes(table_name)}


def upgrade() -> None:
    """Upgrade schema."""
    if not _table_exists("sticker_packs"):
        op.create_table(
            "sticker_packs",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("pack_id", sa.String(length=64), nullable=False),
            sa.Column("owner_id", sa.BigInteger(), nullable=False),
            sa.Column("title", sa.String(length=64), nullable=False),
            sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _index_exists("sticker_packs", "ix_sticker_packs_pack_id"):
        op.create_index("ix_sticker_packs_pack_id", "sticker_packs", ["pack_id"], unique=True)

    if not _index_exists("sticker_packs", "ix_sticker_packs_owner_id"):
        op.create_index("ix_sticker_packs_owner_id", "sticker_packs", ["owner_id"], unique=False)

    if not _index_exists("sticker_packs", "ux_sticker_packs_owner_default"):
        op.create_index(
            "ux_sticker_packs_owner_default",
            "sticker_packs",
            ["owner_id"],
            unique=True,
            postgresql_where=sa.text("is_default = true"),
        )


def downgrade() -> None:
    """Downgrade schema."""
    if _table_exists("sticker_packs"):
        if _index_exists("sticker_packs", "ux_sticker_packs_owner_default"):
            op.drop_index("ux_sticker_packs_owner_default", table_name="sticker_packs")
        if _index_exists("sticker_packs", "ix_sticker_packs_owner_id"):
            op.drop_index("ix_sticker_packs_owner_id", table_name="sticker_packs")
        if _index_exists("sticker_packs", "ix_sticker_packs_pack_id"):
            op.drop_index("ix_sticker_packs_pack_id", table_name="sticker_packs")

        op.drop_table("sticker_packs")
