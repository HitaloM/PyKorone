from datetime import datetime
from typing import List, Optional

from beanie import Document
from pydantic import Field


class Federation(Document):
    """Federation model - matches existing DB schema exactly"""

    fed_name: str
    fed_id: str
    creator: int
    chats: Optional[List[int]] = Field(default_factory=list)
    subscribed: Optional[List[str]] = Field(default_factory=list)
    admins: Optional[List[int]] = Field(default_factory=list)
    log_chat_id: Optional[int] = None

    class Settings:
        name = "feds"
        indexes = [
            "fed_id",  # Primary lookup index
            "creator",  # Creator lookup index
            "chats",  # Chat membership index
        ]


class FederationBan(Document):
    """Federation ban model - matches existing DB schema exactly"""

    fed_id: str
    user_id: int
    banned_chats: Optional[List[int]] = Field(default_factory=list)
    time: datetime
    by: int  # User who performed the ban
    reason: Optional[str] = None
    origin_fed: Optional[str] = None  # For subscribed federation bans

    class Settings:
        name = "fed_bans"
        indexes = [
            [("fed_id", 1), ("user_id", 1)],  # Compound index for fed+user lookup
            "user_id",  # User lookup index
            "fed_id",  # Federation lookup index
        ]
