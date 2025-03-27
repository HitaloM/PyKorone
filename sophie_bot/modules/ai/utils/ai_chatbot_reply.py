from aiogram.types import Message
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool
from pydantic_ai.messages import ModelRequest, ModelResponse, ToolCallPart, ToolReturnPart

from sophie_bot.config import CONFIG
from sophie_bot.db.models import AIMemoryModel
from sophie_bot.middlewares.connections import ChatConnection
from sophie_bot.modules.ai.agent_tools.memory import MemoryAgentTool
from sophie_bot.modules.ai.agent_tools.notes import notes_list_ai_tool
from sophie_bot.modules.ai.utils.ai_header import ai_header
from sophie_bot.modules.ai.utils.ai_models import DEFAULT_PROVIDER
from sophie_bot.modules.ai.utils.ai_tool_context import SophieAIToolContenxt
from sophie_bot.modules.ai.utils.new_ai_chatbot import new_ai_generate
from sophie_bot.modules.ai.utils.new_message_history import NewAIMessageHistory
from sophie_bot.modules.notes.utils.unparse_legacy import legacy_markdown_to_html
from sophie_bot.services.bot import bot
from sophie_bot.utils.i18n import gettext as _
from stfu_tg import PreformattedHTML, Doc, Section, KeyValue, VList


def is_search_in_history(message_history: list[ModelRequest | ModelResponse]) -> bool:
    parts = list(message.parts for message in message_history)
    return any(part for part in parts if
               isinstance(part[0], (ToolCallPart, ToolReturnPart)) and part[0].tool_name == 'duckduckgo_search')


async def ai_chatbot_reply(
        message: Message,
        connection: ChatConnection,
        user_text: str | None
):
    """
    Sends a reply from AI based on user input and message history.
    """

    await bot.send_chat_action(message.chat.id, "typing")

    # Chat memory
    memory_lines = await AIMemoryModel.get_lines(connection.db_model.id)

    system_prompt = Doc(
        _("You can use DuckDuckGo to search for information. Include information sources as links.")
    )
    if memory_lines:
        system_prompt += Section(
            VList(*memory_lines),
            title=_("You have the following information in memory")
        )

    history = NewAIMessageHistory()
    await history.chatbot_history(
        message.chat.id,
        additional_system_prompt=system_prompt.to_md()
    )
    await history.add_from_message_with_reply(message, custom_user_text=user_text)

    model = DEFAULT_PROVIDER
    result = await new_ai_generate(
        history,
        tools=[MemoryAgentTool(), duckduckgo_search_tool(), notes_list_ai_tool()],
        model=model,
        agent_kwargs={"deps": SophieAIToolContenxt(connection=connection)}
    )

    header_items = []
    if is_search_in_history(result.message_history):
        header_items.append("DuckDuckGo Search 🔍")

    doc = Doc(
        ai_header(model, *header_items),
        PreformattedHTML(legacy_markdown_to_html(result.output))
    )

    if CONFIG.debug_mode:
        doc += " "
        doc += Section(
            KeyValue('LLM Requests', result.usage.requests),
            KeyValue('Retries', result.retires),
            KeyValue('Request tokens', result.usage.request_tokens),
            KeyValue('Response tokens', result.usage.response_tokens),
            KeyValue('Total tokens', result.usage.total_tokens),
            KeyValue('Details', result.usage.details or '-'),
            title='DEBUG'
        )

    return await message.reply(doc.to_html(), disable_web_page_preview=True)
