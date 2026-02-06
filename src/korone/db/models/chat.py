from datetime import UTC, datetime
from typing import Any

from aiogram.enums import ChatType
from sqlalchemy import BigInteger, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship  # noqa: TC002

from korone.db.base import Base


class UserInGroupModel(Base):
    __tablename__ = "users_in_groups"
    __table_args__ = (UniqueConstraint("user_id", "group_id", name="ux_users_in_groups_user_group"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("chats.id", ondelete="CASCADE"), index=True)
    group_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("chats.id", ondelete="CASCADE"), index=True)
    first_saw: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    last_saw: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    user: Mapped[ChatModel] = relationship("ChatModel", foreign_keys=[user_id])
    group: Mapped[ChatModel] = relationship("ChatModel", foreign_keys=[group_id])

    def __repr__(self) -> str:
        return (
            f"UserInGroupModel(id={self.id!r}, user_id={self.user_id!r}, "
            f"group_id={self.group_id!r}, first_saw={self.first_saw!r}, "
            f"last_saw={self.last_saw!r})"
        )


class ChatTopicModel(Base):
    __tablename__ = "chat_topics"
    __table_args__ = (UniqueConstraint("group_id", "thread_id", name="ux_chat_topics_group_thread"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("chats.id", ondelete="CASCADE"), index=True)
    thread_id: Mapped[int] = mapped_column(index=True)
    name: Mapped[str | None] = mapped_column(String(128))
    last_active: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    group: Mapped[ChatModel] = relationship("ChatModel", foreign_keys=[group_id])

    def __repr__(self) -> str:
        return (
            f"ChatTopicModel(id={self.id!r}, group_id={self.group_id!r}, "
            f"thread_id={self.thread_id!r}, name={self.name!r}, "
            f"last_active={self.last_active!r})"
        )


class ChatModel(Base):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    type: Mapped[ChatType] = mapped_column(SAEnum(ChatType), index=True)
    first_name_or_title: Mapped[str] = mapped_column(String(256))
    last_name: Mapped[str | None] = mapped_column(String(64))
    username: Mapped[str | None] = mapped_column(String(64), index=True)
    is_bot: Mapped[bool] = mapped_column(default=False)
    first_saw: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    last_saw: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    @staticmethod
    def user_from_id(user_id: int) -> ChatModel:
        return ChatModel(
            chat_id=user_id,
            type=ChatType.PRIVATE,
            first_name_or_title="User",
            last_name=None,
            username=None,
            is_bot=False,
            last_saw=datetime.now(UTC),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "chat_id": self.chat_id,
            "type": self.type,
            "first_name_or_title": self.first_name_or_title,
            "last_name": self.last_name,
            "username": self.username,
            "is_bot": self.is_bot,
            "first_saw": self.first_saw,
            "last_saw": self.last_saw,
        }

    def __repr__(self) -> str:
        return (
            f"ChatModel(id={self.id!r}, chat_id={self.chat_id!r}, type={self.type!r}, "
            f"first_name_or_title={self.first_name_or_title!r}, last_name={self.last_name!r}, "
            f"username={self.username!r}, is_bot={self.is_bot!r}, "
            f"first_saw={self.first_saw!r}, last_saw={self.last_saw!r})"
        )
