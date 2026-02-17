from datetime import UTC, datetime

from sqlalchemy import BigInteger, Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column  # noqa: TC002

from korone.db.base import Base


class StickerPackModel(Base):
    __tablename__ = "sticker_packs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    pack_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    owner_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(64), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    def __repr__(self) -> str:
        return (
            f"StickerPackModel(id={self.id!r}, pack_id={self.pack_id!r}, owner_id={self.owner_id!r}, "
            f"title={self.title!r}, is_default={self.is_default!r}, created_at={self.created_at!r})"
        )
