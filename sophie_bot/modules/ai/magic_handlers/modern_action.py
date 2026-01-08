from typing import Any, Optional

from aiogram.types import CallbackQuery, Message
from pydantic import BaseModel
from stfu_tg import Italic, Section, Title
from stfu_tg.doc import Doc, Element, PreformattedHTML

from sophie_bot.db.models import ChatModel
from sophie_bot.middlewares.connections import ChatConnection
from sophie_bot.modules.ai.filters.throttle import AIThrottleFilter
from sophie_bot.modules.ai.utils.ai_get_provider import get_chat_default_model
from sophie_bot.modules.ai.utils.new_ai_chatbot import new_ai_generate
from sophie_bot.modules.ai.utils.new_message_history import NewAIMessageHistory
from sophie_bot.modules.filters.types.modern_action_abc import (
    ActionSetupMessage,
    ActionSetupTryAgainException,
    ModernActionABC,
    ModernActionSetting,
)
from sophie_bot.modules.notes.utils.unparse_legacy import legacy_markdown_to_html
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


class AIReplyActionDataModel(BaseModel):
    prompt: str


async def set_reply_text(event: Message | CallbackQuery, data: dict[str, Any]) -> AIReplyActionDataModel:
    if isinstance(event, CallbackQuery):
        raise ValueError("This handlers setup_confirm can only be used with messages")

    prompt = event.text

    if not prompt:
        raise ActionSetupTryAgainException(_("Please enter AI prompt"))

    return AIReplyActionDataModel(prompt=prompt)


async def reply_action_setup_message(_event: Message | CallbackQuery, _data: dict[str, Any]) -> ActionSetupMessage:
    text = Doc(
        _("Please send me the AI instruction to proceed!"),
        _("The AI will try to remember the chat context and will respond accordingly!"),
        _("For example, you can combine it with the warn filter: 'Tell the user how bad it is to speak profanity'"),
    ).to_html()

    return ActionSetupMessage(text=text)


class AIReplyAction(ModernActionABC[AIReplyActionDataModel]):
    name = "ai_text"

    icon = "✨"
    title = l_("AI Response")

    interactive_setup = ModernActionSetting(
        title=l_("Reply to message"), setup_message=reply_action_setup_message, setup_confirm=set_reply_text
    )
    data_object = AIReplyActionDataModel

    @staticmethod
    def description(data: AIReplyActionDataModel) -> Element | str:
        return Section(Italic(data.prompt), title=_("Send an AI Respond with prompt"), title_underline=False)

    def settings(self, data: AIReplyActionDataModel) -> dict[str, ModernActionSetting]:
        return {
            "reply_text": ModernActionSetting(
                title=l_("Change AI prompt"),
                icon="✨",
                setup_message=reply_action_setup_message,
                setup_confirm=set_reply_text,
            ),
        }

    async def handle(self, message: Message, data: dict, filter_data: AIReplyActionDataModel) -> Optional[Element]:
        connection: ChatConnection = data["connection"]

        if not (chat_db := await ChatModel.get_by_tid(connection.tid)):
            raise SophieException("Chat not found in database")

        if not (message.text or message.caption and await AIThrottleFilter().__call__(message, chat_db)):
            return

        messages = await NewAIMessageHistory.chatbot(message, additional_system_prompt=filter_data.prompt)
        provider = await get_chat_default_model(connection.db_model.iid)

        result = await new_ai_generate(messages, provider)
        return Doc(Title(_("✨ AI Response")), PreformattedHTML(legacy_markdown_to_html(str(result.output))))
