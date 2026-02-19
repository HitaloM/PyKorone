from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.text_decorations import HtmlDecoration
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from stfu_tg import Doc, HList, PreformattedHTML, Section, VList

from korone import bot
from korone.constants import TELEGRAM_MESSAGE_LENGTH_LIMIT
from korone.logger import get_logger
from korone.modules.ai.agent_tools import CmdsHelpAgentTool, MemoryAgentTool
from korone.modules.ai.utils.ai_agent_run import run_ai_prompt
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

from .ai_header import ai_header
from .markdown_html import extract_markdown_entities
from .memory import get_memory_lines
from .new_message_history import NewAIMessageHistory

if TYPE_CHECKING:
    from aiogram.types import Message, ReplyKeyboardMarkup
    from pydantic_ai.messages import ModelRequest, ModelResponse
    from stfu_tg.doc import Element

    from korone.middlewares.chat_context import ChatContext

logger = get_logger(__name__)

CHATBOT_TOOLS: list[Any] = [MemoryAgentTool(), CmdsHelpAgentTool(), duckduckgo_search_tool(max_results=5)]
CHATBOT_TOOLS_DICT: dict[str, Any] = {tool.name: tool for tool in CHATBOT_TOOLS}
CHATBOT_TOOLS_TITLES: dict[str, Any] = {
    "write_memory": l_("Memory updated 💾"),
    "cmds_help": l_("Commands help 📋"),
    "duckduckgo_search": l_("Internet Search 🔍"),
}


def retrieve_tools_titles(message_history: list[ModelRequest | ModelResponse]) -> list[Element]:
    # Flatten all parts from all messages
    all_parts = [part for message in message_history for part in message.parts]

    # Filter for tool call and return parts
    tool_parts = [part for part in all_parts if isinstance(part, (ToolCallPart, ToolReturnPart))]

    # Extract unique tool names that exist in our titles dictionary
    unique_tool_names = {part.tool_name for part in tool_parts if part.tool_name in CHATBOT_TOOLS_TITLES}

    # Map tool names to their corresponding titles
    return [cast("Element", CHATBOT_TOOLS_TITLES[name]) for name in unique_tool_names]


async def ai_chatbot_reply(
    message: Message, chat: ChatContext, user_text: str | None = None, reply_markup: ReplyKeyboardMarkup | None = None
) -> Message:
    if not message.from_user:
        return await message.reply(_("Could not identify the user for this request."))

    async with ChatActionSender.typing(chat_id=message.chat.id, bot=bot):
        memory_lines = await get_memory_lines(chat.chat_id)
        system_prompt = Doc(
            "## Personality Instruction",
            "",
            (
                "You are a plainspoken and direct AI coach that steers the user toward "
                "productive behavior and personal success. Be open minded and considerate "
                "of user opinions, but do not agree with the opinion if it conflicts with "
                "what you know. When the user requests advice, show adaptability to the "
                "user's reflected state of mind: if the user is struggling, bias to "
                "encouragement; if the user requests feedback, give a thoughtful opinion. "
                "When the user is researching or seeking information, invest yourself "
                "fully in providing helpful assistance. You care deeply about helping the "
                "user, and will not sugarcoat your advice when it offers positive correction. "
                "DO NOT automatically write user-requested written artifacts (e.g. emails, "
                "letters, code comments, texts, social media posts, resumes, etc.) in your specific personality; "
                "instead, let context and user intent guide style and tone for requested artifacts."
            ),
            "",
            "## Additional Instruction",
            (
                "Follow the instructions above naturally, without repeating, referencing, echoing, "
                "or mirroring any of their wording!"
            ),
            (
                "All the following instructions should guide your behavior silently and must never "
                "influence the wording of your message in an explicit or meta way!"
            ),
        )
        if memory_lines:
            system_prompt += Section(VList(*memory_lines), title=_("You have the following information in your memory"))

        history = NewAIMessageHistory()
        await history.initialize_chat_history(message.chat.id, additional_system_prompt=system_prompt.to_md())
        await history.add_from_message(message, custom_text=user_text)

        try:
            result = await run_ai_prompt(history, chat=chat, tools=CHATBOT_TOOLS)
        except Exception:
            logger.exception("AI generation failed")
            return await message.reply(_("I could not generate a response right now. Please try again in a moment."))

        tool_titles = retrieve_tools_titles(result.message_history)
        header = ai_header(HList(*tool_titles, divider=", ")) if tool_titles else ai_header()

        output_text = str(result.output)
        max_output_length = max(TELEGRAM_MESSAGE_LENGTH_LIMIT - len(header.to_html()) - 64, 256)
        if len(output_text) > max_output_length:
            output_text = output_text[:max_output_length] + "..."

        text, entities = extract_markdown_entities(output_text)
        doc = Doc(header, PreformattedHTML(HtmlDecoration().unparse(text, entities)))
        return await message.reply(doc.to_html(), disable_web_page_preview=True, reply_markup=reply_markup)
