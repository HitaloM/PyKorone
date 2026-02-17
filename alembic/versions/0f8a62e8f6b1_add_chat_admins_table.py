"""add_chat_admins_table

Revision ID: 0f8a62e8f6b1
Revises: ab07d3f76f2a
Create Date: 2026-02-17 16:55:00.000000

"""

from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence


# revision identifiers, used by Alembic.
revision: str = "0f8a62e8f6b1"
down_revision: str | Sequence[str] | None = "ab07d3f76f2a"
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
    if not _table_exists("chat_admins"):
        op.create_table(
            "chat_admins",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("chat_id", sa.BigInteger(), nullable=False),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("data", sa.JSON(), nullable=False),
            sa.Column("last_updated", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["chat_id"], ["chats.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["chats.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("chat_id", "user_id", name="ux_chat_admins_chat_user"),
        )

    if not _index_exists("chat_admins", "ix_chat_admins_chat_id"):
        op.create_index("ix_chat_admins_chat_id", "chat_admins", ["chat_id"], unique=False)
    if not _index_exists("chat_admins", "ix_chat_admins_user_id"):
        op.create_index("ix_chat_admins_user_id", "chat_admins", ["user_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    if _table_exists("chat_admins"):
        if _index_exists("chat_admins", "ix_chat_admins_user_id"):
            op.drop_index("ix_chat_admins_user_id", table_name="chat_admins")
        if _index_exists("chat_admins", "ix_chat_admins_chat_id"):
            op.drop_index("ix_chat_admins_chat_id", table_name="chat_admins")
        op.drop_table("chat_admins")
