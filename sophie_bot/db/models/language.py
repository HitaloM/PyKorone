from typing import Annotated

from beanie import Document, Indexed


class LanguageModel(Document):
    # Old ID
    chat_id: Annotated[int, Indexed(unique=True)]

    # New link
    # chat: Link[ChatModel]

    lang: str

    class Settings:
        name = "lang"
