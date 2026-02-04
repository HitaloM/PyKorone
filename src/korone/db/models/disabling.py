from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column  # noqa: TC002

from korone.db.base import Base


class DisablingModel(Base):
    __tablename__ = "disabled"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(unique=True, index=True)
    cmds: Mapped[list[str]] = mapped_column(JSON, default=list)

    def __repr__(self) -> str:
        return f"DisablingModel(id={self.id!r}, chat_id={self.chat_id!r}, cmds={self.cmds!r})"
