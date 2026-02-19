from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram.filters import Filter

from korone import aredis
from korone.modules.ai.utils.keys import ai_throttle_key

if TYPE_CHECKING:
    from aiogram.types import Message

DEFAULT_AI_THROTTLE_SECONDS = 5


class AIThrottleFilter(Filter):
    def __init__(self, seconds: int = DEFAULT_AI_THROTTLE_SECONDS) -> None:
        self.seconds = max(seconds, 1)

    async def __call__(self, message: Message) -> bool:
        if not message.from_user:
            return False

        key = ai_throttle_key(message.chat.id, message.from_user.id)
        created = await aredis.set(key, "1", ex=self.seconds, nx=True)
        return bool(created)
