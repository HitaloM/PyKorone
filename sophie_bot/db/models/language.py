from typing import Annotated

from beanie import Document, Indexed, Link

from sophie_bot.db.models import ChatModel


class LanguageModel(Document):
    # Old ID
    chat_id: Annotated[int, Indexed(unique=True)]

    # New link
    chat: Annotated[Link[ChatModel], Indexed(unique=True)]

    lang: str

    class Settings:
        name = "lang"
