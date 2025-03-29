from aiogram.types import Message
from pydantic_ai import Tool
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool
from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    ToolCallPart,
    ToolReturnPart,
)
from stfu_tg import Doc, HList, PreformattedHTML, Section, VList
from stfu_tg.doc import Element

from sophie_bot.db.models import AIMemoryModel
from sophie_bot.middlewares.connections import ChatConnection
from sophie_bot.modules.ai.agent_tools.memory import MemoryAgentTool
from sophie_bot.modules.ai.utils.ai_header import ai_header
from sophie_bot.modules.ai.utils.ai_models import DEFAULT_PROVIDER
from sophie_bot.modules.ai.utils.ai_tool_context import SophieAIToolContenxt
from sophie_bot.modules.ai.utils.new_ai_chatbot import new_ai_generate
from sophie_bot.modules.ai.utils.new_message_history import NewAIMessageHistory
from sophie_bot.modules.notes.utils.unparse_legacy import legacy_markdown_to_html
from sophie_bot.services.bot import bot
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_

CHATBOT_TOOLS = [
    MemoryAgentTool(),
    duckduckgo_search_tool(),
    # notes_list_ai_tool(),
]
CHATBOT_TOOLS_DICT: dict[str, Tool] = {tool.name: tool for tool in CHATBOT_TOOLS}
CHATBOT_TOOLS_TITLES = {
    "write_memory": l_("Memory updated 💾"),
    "duckduckgo_search": l_("DuckDuckGo Search 🔍"),
    "get_notes": l_("Scanned notes 🗒"),
}


def retrieve_tools_titles(message_history: list[ModelRequest | ModelResponse]) -> list[Element]:
    # Flatten all parts from all messages
    all_parts = [part for message in message_history for part in message.parts]

    # Filter for tool call and return parts
    tool_parts = [part for part in all_parts if isinstance(part, ToolCallPart) or isinstance(part, ToolReturnPart)]

    # Extract unique tool names that exist in our titles dictionary
    unique_tool_names = {part.tool_name for part in tool_parts if part.tool_name in CHATBOT_TOOLS_TITLES}

    # Map tool names to their corresponding titles
    return [CHATBOT_TOOLS_TITLES[name] for name in unique_tool_names]


async def ai_chatbot_reply(message: Message, connection: ChatConnection, user_text: str | None = None):
    """
    Sends a reply from AI based on user input and message history.
    """

    if not connection.db_model:
        return

    await bot.send_chat_action(message.chat.id, "typing")

    # Chat memory
    memory_lines = await AIMemoryModel.get_lines(connection.db_model.id)

    system_prompt = Doc(
        _("You can use DuckDuckGo to search for information. Include information sources as links."),
        _("You can also save important facts to memory."),
    )
    if memory_lines:
        system_prompt += Section(VList(*memory_lines), title=_("You have the following information in memory"))

    history = NewAIMessageHistory()
    await history.chatbot_history(message.chat.id, additional_system_prompt=system_prompt.to_md())
    await history.add_from_message(message, custom_text=user_text)

    model = DEFAULT_PROVIDER
    result = await new_ai_generate(
        history, tools=CHATBOT_TOOLS, model=model, agent_kwargs={"deps": SophieAIToolContenxt(connection=connection)}
    )

    header_items = [*retrieve_tools_titles(result.message_history), HList(divider=", ")]

    doc = Doc(ai_header(model, *header_items), PreformattedHTML(legacy_markdown_to_html(result.output)))

    # if CONFIG.debug_mode:
    #     doc += " "
    #     doc += Section(
    #         KeyValue('LLM Requests', result.usage.requests),
    #         KeyValue('Retries', result.retires),
    #         KeyValue('Request tokens', result.usage.request_tokens),
    #         KeyValue('Response tokens', result.usage.response_tokens),
    #         KeyValue('Total tokens', result.usage.total_tokens),
    #         KeyValue('Details', result.usage.details or '-'),
    #         title='DEBUG'
    #     )

    return await message.reply(doc.to_html(), disable_web_page_preview=True)
