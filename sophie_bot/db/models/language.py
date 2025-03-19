from typing import Annotated

from beanie import Document, Indexed

from sophie_bot.config import CONFIG


class LanguageModel(Document):
    # Old ID
    chat_id: Annotated[int, Indexed(unique=True)]

    # New link
    # chat: Link[ChatModel]

    lang: str

    class Settings:
        name = "lang"

    @staticmethod
    async def get_locale(chat_id: int) -> str:
        item = await LanguageModel.find_one(LanguageModel.chat_id == chat_id)
        return item.lang if item else CONFIG.default_locale
