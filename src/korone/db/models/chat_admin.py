from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship  # noqa: TC002

from korone.db.base import Base

if TYPE_CHECKING:
    from korone.db.models.chat import ChatModel


class ChatAdminModel(Base):
    __tablename__ = "chat_admins"
    __table_args__ = (UniqueConstraint("chat_id", "user_id", name="ux_chat_admins_chat_user"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("chats.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("chats.id", ondelete="CASCADE"), index=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    chat: Mapped[ChatModel] = relationship("ChatModel", foreign_keys=[chat_id])
    user: Mapped[ChatModel] = relationship("ChatModel", foreign_keys=[user_id])

    def __repr__(self) -> str:
        return (
            f"ChatAdminModel(id={self.id!r}, chat_id={self.chat_id!r}, "
            f"user_id={self.user_id!r}, last_updated={self.last_updated!r})"
        )
