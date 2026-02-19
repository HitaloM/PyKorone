from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiogram import flags
from ass_tg.types import OptionalArg, TextArg

from korone.filters.chat_status import GroupChatFilter
from korone.filters.cmd import CMDFilter
from korone.modules.ai.filters.ai_enabled import AIEnabledFilter
from korone.modules.ai.utils.ai_chatbot_reply import ai_chatbot_reply
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import Message
    from ass_tg.types.base_abc import ArgFabric


@flags.help(description=l_("Ask Korone AI in the current chat"))
@flags.disableable(name="ai")
class AiCmdHandler(KoroneMessageHandler):
    @classmethod
    async def handler_args(cls, message: Message | None, data: dict[str, Any]) -> dict[str, ArgFabric]:
        return {"text": OptionalArg(TextArg(l_("Prompt")))}

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter("ai"), GroupChatFilter(), AIEnabledFilter())

    async def handle(self) -> Message | None:
        user_text: str | None = self.data.get("text")
        if not user_text:
            await self.event.reply(_("Please provide a prompt after /ai."))
            return None

        return await ai_chatbot_reply(self.event, self.chat, user_text=user_text)
