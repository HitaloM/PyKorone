from aiogram.types import Message
from pydantic_ai import Tool
from pydantic_ai.common_tools.tavily import tavily_search_tool
from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    ToolCallPart,
    ToolReturnPart,
)
from pydantic_ai.models import Model
from stfu_tg import BlockQuote, Doc, HList, KeyValue, PreformattedHTML, Section, VList, Template
from stfu_tg.doc import Element

from sophie_bot.config import CONFIG
from sophie_bot.db.models import AIMemoryModel
from sophie_bot.metrics import track_ai_conversation, track_ai_usage
from sophie_bot.middlewares.connections import ChatConnection
from sophie_bot.modules.ai.agent_tools.cmds_help import CmdsHelpAgentTool
from sophie_bot.modules.ai.agent_tools.memory import MemoryAgentTool
from sophie_bot.modules.ai.utils.ai_get_provider import get_chat_default_model
from sophie_bot.modules.ai.utils.ai_header import ai_header
from sophie_bot.modules.ai.utils.ai_models import AI_MODEL_TO_SHORT_NAME
from sophie_bot.modules.ai.utils.ai_tool_context import SophieAIToolContenxt
from sophie_bot.modules.ai.utils.new_ai_chatbot import new_ai_generate
from sophie_bot.modules.ai.utils.new_message_history import NewAIMessageHistory
from sophie_bot.modules.help.utils.extract_info import HELP_MODULES
from sophie_bot.modules.notes.utils.unparse_legacy import legacy_markdown_to_html
from sophie_bot.services.bot import bot
from sophie_bot.utils.feature_flags import is_enabled
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_

CHATBOT_TOOLS = [
    MemoryAgentTool(),
    CmdsHelpAgentTool(),
    tavily_search_tool(api_key=CONFIG.tavily_api_key),
    # notes_list_ai_tool(),
]
CHATBOT_TOOLS_DICT: dict[str, Tool] = {tool.name: tool for tool in CHATBOT_TOOLS}
CHATBOT_TOOLS_TITLES = {
    "write_memory": l_("Memory updated 💾"),
    "cmds_help": l_("Commands help 📋"),
    "tavily_search": l_("Internet Search 🔍"),
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


async def ai_chatbot_reply(
    message: Message,
    connection: ChatConnection,
    user_text: str | None = None,
    debug_mode: bool = False,
    model: Model | None = None,
    **kwargs,
):
    """
    Sends a reply from AI based on user input and message history.
    """

    # Global kill-switch: AI Chatbot
    if not await is_enabled("ai_chatbot"):
        return

    if not connection.db_model:
        return

    # Track active AI conversation
    async with track_ai_conversation():
        await bot.send_chat_action(message.chat.id, "typing")

        # Chat memory
        memory_lines = await AIMemoryModel.get_lines(connection.db_model.iid)

        system_prompt = Doc(
            _("You can use Tavily to search for information. Include information sources as links."),
            _("You can also save important things to the memory."),
            _(
                "If the user asks anything regarding using Sophie bot, make sure to execute `cmds_help` tool to obtain a help context, do not search internet for bot information."
            ),
            Template(_("Available Sophie modules: {modules}"), modules=HList(*HELP_MODULES.keys())),
        )
        if memory_lines:
            system_prompt += Section(VList(*memory_lines), title=_("You have the following information in your memory"))

        history = NewAIMessageHistory()
        await history.initialize_chat_history(message.chat.id, additional_system_prompt=system_prompt.to_md())
        await history.add_from_message(message, custom_text=user_text)

        # Debug mode
        debug_mode = debug_mode or CONFIG.debug_mode
        if "^llm_debug" in (user_text or message.text or ""):
            debug_mode = True

        # History debug
        if debug_mode:
            await message.reply(
                Section(BlockQuote(history.history_debug(), expandable=True), title="LLM History").to_html(),
                disable_web_page_preview=True,
            )

        if model is None:
            model = await get_chat_default_model(connection.db_model.iid)  # type: ignore
        result = await new_ai_generate(
            history,
            tools=CHATBOT_TOOLS,
            model=model,
            agent_kwargs={"deps": SophieAIToolContenxt(connection=connection)},
        )

        # Track AI usage metrics
        if result.usage:
            track_ai_usage(model, result.usage)

        header_items = [*retrieve_tools_titles(result.message_history), HList(divider=", ")]
        header = ai_header(model, *header_items)

        # Split if too long
        output_text = str(result.output)
        length = len(output_text) + len(header.to_html())
        if length > 4000:
            output_text = output_text[:4000] + "..."

        doc = Doc(header, BlockQuote(PreformattedHTML(legacy_markdown_to_html(output_text, extract_headings=True))))
        if debug_mode:
            doc += " "
            doc += Section(
                BlockQuote(
                    Doc(
                        KeyValue("Model", AI_MODEL_TO_SHORT_NAME[model.model_name]),
                        KeyValue("LLM Requests", result.usage.requests),
                        KeyValue("Retries", result.retries),
                        KeyValue("Request tokens", result.usage.request_tokens),
                        KeyValue("Response tokens", result.usage.response_tokens),
                        KeyValue("Total tokens", result.usage.total_tokens),
                        KeyValue("Details", result.usage.details or "-"),
                    ),
                    expandable=True,
                ),
                title="Provider debug",
            )

        return await message.reply(doc.to_html(), disable_web_page_preview=True, **kwargs)
