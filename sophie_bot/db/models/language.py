from typing import Annotated

from beanie import Document, Indexed


class LanguageModel(Document):
    chat_id: Annotated[int, Indexed(unique=True)]
    lang: str

    class Settings:
        name = "lang"
