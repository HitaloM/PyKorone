from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from korone.middlewares.chat_context import ChatContext


@dataclass(slots=True, frozen=True)
class KoroneAIToolContext:
    chat: ChatContext

    @property
    def chat_id(self) -> int:
        return self.chat.chat_id
