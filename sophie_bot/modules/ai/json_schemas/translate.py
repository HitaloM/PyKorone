from typing import Optional

from pydantic import BaseModel, Field


class AITranslateResponseSchema(BaseModel):
    needs_translation: bool = Field(
        description="Whatever the provided text needs translation, false if the text is already on the target language")
    origin_language_name: str = Field(description="Origin language of the text")
    origin_language_emoji: str = Field(description="Flag of the origin language")
    translated_text: str = Field(description="Translated text, word to word with original")
    translation_explanations: Optional[str] = Field(
        description="Briefly any explanations or clarifications for the translation, none if not applicable"
    )
