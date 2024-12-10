from typing import Any, TypeVar

from pydantic import BaseModel

ACTION_DATA_DUMPED = dict[str, Any] | None
ACTION_DATA = TypeVar("ACTION_DATA", bound=BaseModel | None)
