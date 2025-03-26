from aiogram.types import Message
from pydantic_ai.messages import ModelRequest, ModelResponse, ToolCallPart

from sophie_bot.config import CONFIG
from sophie_bot.modules.ai.utils.ai_header import ai_header
from sophie_bot.modules.ai.utils.ai_models import DEFAULT_PROVIDER
from sophie_bot.modules.ai.utils.new_ai_chatbot import new_ai_generate
from sophie_bot.modules.ai.utils.new_message_history import NewAIMessageHistory
from sophie_bot.modules.notes.utils.unparse_legacy import legacy_markdown_to_html
from sophie_bot.services.bot import bot
from stfu_tg import PreformattedHTML, Doc, Section, KeyValue


def is_search_in_history(message_history: list[ModelRequest | ModelResponse]) -> bool:
    parts = list(message.parts for message in message_history)
    return any(part for part in parts if isinstance(part[0], ToolCallPart) and part[0].tool_name == 'duckduckgo_search')


async def ai_chatbot_reply(
        message: Message,
        user_text: str
):
    """
    Sends a reply from AI based on user input and message history.
    """

    await bot.send_chat_action(message.chat.id, "typing")

    history = NewAIMessageHistory()
    await history.chatbot_history(message.chat.id,
                                  additional_system_prompt="Use DuckDuckGo to search for information. Include information sources as links.")

    model = DEFAULT_PROVIDER
    result = await new_ai_generate(
        user_text,
        history=history,
        model=model
    )

    header_items = []
    if is_search_in_history(result.message_history):
        header_items.append("Internet search 🌍")

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

    await message.reply(doc.to_html(), disable_web_page_preview=True)
