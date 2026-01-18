from __future__ import annotations
from pydantic import BaseModel
from sophie_bot.db.models.ai.ai_moderator import DetectionLevel


class ModeratorSettingsResponse(BaseModel):
    enabled: bool
    sexual: DetectionLevel
    hate_and_discrimination: DetectionLevel
    violence_and_threats: DetectionLevel
    dangerous_and_criminal_content: DetectionLevel
    selfharm: DetectionLevel
    health: DetectionLevel
    financial: DetectionLevel
    law: DetectionLevel
    pii: DetectionLevel


class ModeratorSettingsUpdate(BaseModel):
    enabled: bool | None = None
    sexual: DetectionLevel | None = None
    hate_and_discrimination: DetectionLevel | None = None
    violence_and_threats: DetectionLevel | None = None
    dangerous_and_criminal_content: DetectionLevel | None = None
    selfharm: DetectionLevel | None = None
    health: DetectionLevel | None = None
    financial: DetectionLevel | None = None
    law: DetectionLevel | None = None
    pii: DetectionLevel | None = None
