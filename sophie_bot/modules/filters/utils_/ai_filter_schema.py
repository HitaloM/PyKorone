from __future__ import annotations

from pydantic import BaseModel, Field


class AIFilterResponseSchema(BaseModel):
    """Schema for AI filter evaluation response."""

    matches: bool = Field(
        description="Whether the message content matches the filter criteria described in the user prompt"
    )
    reasoning: str = Field(description="Brief explanation of why the content does or does not match the criteria")
