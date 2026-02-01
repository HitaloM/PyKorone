from datetime import UTC, datetime

from aiogram.enums import ChatType
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship  # noqa: TC002

from korone.db.base import Base, ModelMixin


class UserInGroupModel(Base, ModelMixin):
    __tablename__ = "users_in_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), index=True)
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), index=True)
    first_saw: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    last_saw: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    user: Mapped[ChatModel] = relationship("ChatModel", foreign_keys=[user_id])
    group: Mapped[ChatModel] = relationship("ChatModel", foreign_keys=[group_id])


class ChatTopicModel(Base, ModelMixin):
    __tablename__ = "chat_topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), index=True)
    thread_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_active: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    group: Mapped[ChatModel] = relationship("ChatModel", foreign_keys=[group_id])


class ChatModel(Base, ModelMixin):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    type: Mapped[ChatType] = mapped_column(SAEnum(ChatType), index=True)
    first_name_or_title: Mapped[str] = mapped_column(String(128))
    last_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    is_bot: Mapped[bool] = mapped_column(Boolean, default=False)
    first_saw: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    last_saw: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    @staticmethod
    def user_from_id(user_id: int) -> ChatModel:
        return ChatModel(
            chat_id=user_id,
            first_name_or_title="User",
            is_bot=False,
            username=None,
            type=ChatType.PRIVATE,
            last_saw=datetime.now(UTC),
        )
