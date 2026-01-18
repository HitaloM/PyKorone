from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict

from sophie_bot.db.models.notes_buttons import Button


class RestSaveable(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    text: Optional[str] = ""
    buttons: list[list[Button]] = []
    preview: Optional[bool] = False
