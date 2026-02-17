"""move_language_to_chats

Revision ID: ab07d3f76f2a
Revises: 1fc8a372560c
Create Date: 2026-02-17 16:20:00.000000

"""

from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence


# revision identifiers, used by Alembic.
revision: str = "ab07d3f76f2a"
down_revision: str | Sequence[str] | None = "1fc8a372560c"
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


def upgrade() -> None:
    """Upgrade schema."""
    if not _column_exists("chats", "language_code"):
        op.add_column("chats", sa.Column("language_code", sa.String(length=16), nullable=True))

    if _table_exists("lang"):
        op.execute(
            sa.text(
                """
                UPDATE chats AS c
                SET language_code = l.lang
                FROM lang AS l
                WHERE c.chat_id = l.chat_id
                """
            )
        )

        if _index_exists("lang", "ix_lang_chat_id"):
            op.drop_index("ix_lang_chat_id", table_name="lang")
        op.drop_table("lang")


def downgrade() -> None:
    """Downgrade schema."""
    if not _table_exists("lang"):
        op.create_table(
            "lang",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("chat_id", sa.BigInteger(), nullable=False),
            sa.Column("lang", sa.String(length=16), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_lang_chat_id", "lang", ["chat_id"], unique=True)

    if _column_exists("chats", "language_code"):
        op.execute(
            sa.text(
                """
                INSERT INTO lang (chat_id, lang)
                SELECT chat_id, language_code
                FROM chats
                WHERE language_code IS NOT NULL
                ON CONFLICT (chat_id) DO UPDATE
                SET lang = EXCLUDED.lang
                """
            )
        )
        op.drop_column("chats", "language_code")
