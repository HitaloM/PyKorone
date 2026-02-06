from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column  # noqa: TC002

from korone.db.base import Base


class LanguageModel(Base):
    __tablename__ = "lang"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    lang: Mapped[str] = mapped_column(String(16))

    def __repr__(self) -> str:
        return f"LanguageModel(id={self.id!r}, chat_id={self.chat_id!r}, lang={self.lang!r})"
