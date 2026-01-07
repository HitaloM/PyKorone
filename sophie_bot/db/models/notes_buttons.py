from typing import Any, Optional

from pydantic import BaseModel

from .button_action import ButtonAction


class Button(BaseModel):
    text: str
    action: ButtonAction
    data: Optional[Any] = None
