"""baseline_schema

Revision ID: 1fc8a372560c
Revises:
Create Date: 2026-02-17 14:37:18.104177

"""

from typing import TYPE_CHECKING

import sqlalchemy as sa

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence


# revision identifiers, used by Alembic.
revision: str = "1fc8a372560c"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "chats",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "type", sa.Enum("SENDER", "PRIVATE", "GROUP", "SUPERGROUP", "CHANNEL", name="chattype"), nullable=False
        ),
        sa.Column("first_name_or_title", sa.String(length=256), nullable=False),
        sa.Column("last_name", sa.String(length=64), nullable=True),
        sa.Column("username", sa.String(length=64), nullable=True),
        sa.Column("is_bot", sa.Boolean(), nullable=False),
        sa.Column("first_saw", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_saw", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chats_chat_id", "chats", ["chat_id"], unique=True)
    op.create_index("ix_chats_type", "chats", ["type"], unique=False)
    op.create_index("ix_chats_username", "chats", ["username"], unique=False)

    op.create_table(
        "disabled",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("cmds", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_disabled_chat_id", "disabled", ["chat_id"], unique=True)

    op.create_table(
        "lang",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("lang", sa.String(length=16), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_lang_chat_id", "lang", ["chat_id"], unique=True)

    op.create_table(
        "lastfm_users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_lastfm_users_chat_id", "lastfm_users", ["chat_id"], unique=True)

    op.create_table(
        "chat_topics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("group_id", sa.BigInteger(), nullable=False),
        sa.Column("thread_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=True),
        sa.Column("last_active", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["chats.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("group_id", "thread_id", name="ux_chat_topics_group_thread"),
    )
    op.create_index("ix_chat_topics_group_id", "chat_topics", ["group_id"], unique=False)
    op.create_index("ix_chat_topics_thread_id", "chat_topics", ["thread_id"], unique=False)

    op.create_table(
        "users_in_groups",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("group_id", sa.BigInteger(), nullable=False),
        sa.Column("first_saw", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_saw", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["chats.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["chats.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "group_id", name="ux_users_in_groups_user_group"),
    )
    op.create_index("ix_users_in_groups_group_id", "users_in_groups", ["group_id"], unique=False)
    op.create_index("ix_users_in_groups_user_id", "users_in_groups", ["user_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_users_in_groups_user_id", table_name="users_in_groups")
    op.drop_index("ix_users_in_groups_group_id", table_name="users_in_groups")
    op.drop_table("users_in_groups")

    op.drop_index("ix_chat_topics_thread_id", table_name="chat_topics")
    op.drop_index("ix_chat_topics_group_id", table_name="chat_topics")
    op.drop_table("chat_topics")

    op.drop_index("ix_lastfm_users_chat_id", table_name="lastfm_users")
    op.drop_table("lastfm_users")

    op.drop_index("ix_lang_chat_id", table_name="lang")
    op.drop_table("lang")

    op.drop_index("ix_disabled_chat_id", table_name="disabled")
    op.drop_table("disabled")

    op.drop_index("ix_chats_username", table_name="chats")
    op.drop_index("ix_chats_type", table_name="chats")
    op.drop_index("ix_chats_chat_id", table_name="chats")
    op.drop_table("chats")
    op.execute("DROP TYPE IF EXISTS chattype")
