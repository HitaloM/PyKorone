from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InstaData:
    media_url: str
    username: str
    description: str
    media_type: str
