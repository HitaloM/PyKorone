from pydantic import BaseModel, Field


class AIUpdateNoteData(BaseModel):
    description: str = Field(
        description="A short snapshot of the idea of the note. A sentence no longer than 50 characters"
    )
