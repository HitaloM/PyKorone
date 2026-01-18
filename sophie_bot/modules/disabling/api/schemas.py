from __future__ import annotations

from pydantic import BaseModel


class DisabledResponse(BaseModel):
    disabled: list[str]


class DisableableResponse(BaseModel):
    disableable: list[str]


class DisabledPayload(BaseModel):
    disabled: list[str]
