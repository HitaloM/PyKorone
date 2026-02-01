from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column  # noqa: TC002

from korone.db.base import Base, ModelMixin


class LanguageModel(Base, ModelMixin):
    __tablename__ = "lang"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    lang: Mapped[str] = mapped_column(String(16))

    @property
    def locale_name(self) -> str:
        return self.lang
