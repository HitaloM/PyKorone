from datetime import UTC, datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column  # noqa: TC002

from korone.db.base import Base


class LastFMUserModel(Base):
    __tablename__ = "lastfm_users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(unique=True, index=True)
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    def __repr__(self) -> str:
        return (
            f"LastFMUserModel(id={self.id!r}, chat_id={self.chat_id!r}, "
            f"username={self.username!r}, updated_at={self.updated_at!r})"
        )
