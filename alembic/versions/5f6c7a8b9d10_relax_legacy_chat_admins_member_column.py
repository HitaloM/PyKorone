"""relax_legacy_chat_admins_member_column

Revision ID: 5f6c7a8b9d10
Revises: 3a7d9d5b1f2c
Create Date: 2026-02-17 19:05:00.000000

"""

from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence


# revision identifiers, used by Alembic.
revision: str = "5f6c7a8b9d10"
down_revision: str | Sequence[str] | None = "3a7d9d5b1f2c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    return table_name in inspect(bind).get_table_names()


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    return column_name in {column["name"] for column in inspect(bind).get_columns(table_name)}


def upgrade() -> None:
    """Upgrade schema."""
    if _table_exists("chat_admins") and _column_exists("chat_admins", "member"):
        op.execute(sa.text("ALTER TABLE chat_admins ALTER COLUMN member DROP NOT NULL"))


def downgrade() -> None:
    """Downgrade schema."""
