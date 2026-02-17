"""fix_legacy_chat_admins_schema

Revision ID: 3a7d9d5b1f2c
Revises: 0f8a62e8f6b1
Create Date: 2026-02-17 18:55:00.000000

"""

from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence


# revision identifiers, used by Alembic.
revision: str = "3a7d9d5b1f2c"
down_revision: str | Sequence[str] | None = "0f8a62e8f6b1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    return table_name in inspect(bind).get_table_names()


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    return column_name in {column["name"] for column in inspect(bind).get_columns(table_name)}


def _index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    return index_name in {index["name"] for index in inspect(bind).get_indexes(table_name)}


def _has_unique_chat_user(table_name: str) -> bool:
    bind = op.get_bind()
    table_inspector = inspect(bind)

    for unique in table_inspector.get_unique_constraints(table_name):
        if set(unique.get("column_names") or []) == {"chat_id", "user_id"}:
            return True

    for index in table_inspector.get_indexes(table_name):
        if index.get("unique") and set(index.get("column_names") or []) == {"chat_id", "user_id"}:
            return True

    return False


def _build_data_from_legacy_columns() -> None:
    legacy_columns = [
        "status",
        "is_anonymous",
        "can_post_messages",
        "can_edit_messages",
        "can_delete_messages",
        "can_restrict_members",
        "can_promote_members",
        "can_change_info",
        "can_invite_users",
        "can_pin_messages",
    ]
    existing_columns = [column for column in legacy_columns if _column_exists("chat_admins", column)]
    if not existing_columns:
        return

    json_pairs = ", ".join(f"'{column}', {column}" for column in existing_columns)
    op.execute(sa.text(f"UPDATE chat_admins SET data = jsonb_build_object({json_pairs})::json WHERE data IS NULL"))


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

    if not _column_exists("chat_admins", "data"):
        op.add_column("chat_admins", sa.Column("data", sa.JSON(), nullable=True))
        _build_data_from_legacy_columns()
        op.execute(sa.text("UPDATE chat_admins SET data = '{}'::json WHERE data IS NULL"))
        op.alter_column("chat_admins", "data", nullable=False)

    if not _column_exists("chat_admins", "last_updated"):
        op.add_column("chat_admins", sa.Column("last_updated", sa.DateTime(timezone=True), nullable=True))
        if _column_exists("chat_admins", "updated_at"):
            op.execute(sa.text("UPDATE chat_admins SET last_updated = updated_at WHERE last_updated IS NULL"))
        else:
            op.execute(
                sa.text("UPDATE chat_admins SET last_updated = NOW() - INTERVAL '7 days' WHERE last_updated IS NULL")
            )
        op.alter_column("chat_admins", "last_updated", nullable=False)

    if not _has_unique_chat_user("chat_admins"):
        op.create_unique_constraint("ux_chat_admins_chat_user", "chat_admins", ["chat_id", "user_id"])

    if not _index_exists("chat_admins", "ix_chat_admins_chat_id"):
        op.create_index("ix_chat_admins_chat_id", "chat_admins", ["chat_id"], unique=False)
    if not _index_exists("chat_admins", "ix_chat_admins_user_id"):
        op.create_index("ix_chat_admins_user_id", "chat_admins", ["user_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
