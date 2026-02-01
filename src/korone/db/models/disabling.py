from sqlalchemy import JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column  # noqa: TC002

from korone.db.base import Base, ModelMixin


class DisablingModel(Base, ModelMixin):
    __tablename__ = "disabled"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    cmds: Mapped[list[str]] = mapped_column(JSON, default=list)
