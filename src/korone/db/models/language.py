from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from korone.config import CONFIG
from korone.db.base import AsyncModelMixin, Base, get_one
from korone.db.session import session_scope


class LanguageModel(Base, AsyncModelMixin):
    __tablename__ = "lang"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    lang: Mapped[str] = mapped_column(String(16))

    @property
    def locale_name(self) -> str:
        return self.lang

    @staticmethod
    async def get_locale(chat_id: int) -> str:
        async with session_scope() as session:
            item = await get_one(session, LanguageModel, LanguageModel.chat_id == chat_id)
        return item.lang if item else CONFIG.default_locale

    @staticmethod
    async def set_locale(chat_id: int, lang: str) -> "LanguageModel":
        async with session_scope() as session:
            item = await get_one(session, LanguageModel, LanguageModel.chat_id == chat_id)
            if item:
                item.lang = lang
                session.add(item)
                return item

            item = LanguageModel(chat_id=chat_id, lang=lang)
            session.add(item)
            await session.flush()
            return item
