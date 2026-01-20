from typing import List, Optional
from pydantic import BaseModel, Field


class WarnResponse(BaseModel):
    id: str
    user_id: int
    admin_id: int
    reason: Optional[str]
    date: str


class WarnSettingsResponse(BaseModel):
    max_warns: int
    actions: List[dict]


class WarnSettingsUpdate(BaseModel):
    max_warns: Optional[int] = Field(None, ge=2, le=10000)
