from korone.config import CONFIG
from korone.db.base import get_one
from korone.db.models.chat import ChatModel
from korone.db.session import session_scope


class LanguageRepository:
    @staticmethod
    async def get_locale(chat_id: int) -> str:
        async with session_scope() as session:
            item = await get_one(session, ChatModel, ChatModel.chat_id == chat_id)
        return item.language_code if item and item.language_code else CONFIG.default_locale

    @staticmethod
    async def set_locale(chat_id: int, lang: str) -> ChatModel:
        async with session_scope() as session:
            if item := await get_one(session, ChatModel, ChatModel.chat_id == chat_id):
                item.language_code = lang
                return item

        msg = "Chat not found"
        raise LookupError(msg)
