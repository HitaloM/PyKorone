from korone.config import CONFIG
from korone.db.base import get_one
from korone.db.models.language import LanguageModel
from korone.db.session import session_scope


class LanguageRepository:
    @staticmethod
    async def get_locale(chat_id: int) -> str:
        async with session_scope() as session:
            item = await get_one(session, LanguageModel, LanguageModel.chat_id == chat_id)
        return item.lang if item else CONFIG.default_locale

    @staticmethod
    async def set_locale(chat_id: int, lang: str) -> LanguageModel:
        async with session_scope() as session:
            if item := await get_one(session, LanguageModel, LanguageModel.chat_id == chat_id):
                item.lang = lang
                return item

            item = LanguageModel(chat_id=chat_id, lang=lang)
            session.add(item)
            await session.flush()
            return item
