from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

from .button_action import ButtonAction


class Button(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    text: str
    action: ButtonAction
    data: Optional[Any] = None
