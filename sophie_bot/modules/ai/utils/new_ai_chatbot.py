from typing import Optional, TypeVar

from aiogram.types import Message, ReplyKeyboardMarkup
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.providers import Provider

from sophie_bot.modules.ai.utils.ai_agent_run import AIAgentResult, ai_agent_run
from sophie_bot.modules.ai.utils.ai_models import DEFAULT_PROVIDER
from sophie_bot.modules.ai.utils.new_message_history import NewAIMessageHistory

RESPONSE_TYPE = TypeVar("RESPONSE_TYPE", bound=BaseModel)


async def new_ai_generate(
        history: NewAIMessageHistory, model: Provider = DEFAULT_PROVIDER, agent_kwargs=None, **kwargs
) -> AIAgentResult:
    """
    Used to generate the AI Chat-bot result text
    """
    if agent_kwargs is None:
        agent_kwargs = dict()

    agent = Agent(model, **kwargs)  # type: ignore
    result = await ai_agent_run(
        agent, user_prompt=history.prompt, message_history=history.message_history, **agent_kwargs
    )
    return result


async def new_ai_generate_schema(
        history: NewAIMessageHistory,
        schema: type[RESPONSE_TYPE],
        model: Provider = DEFAULT_PROVIDER
) -> RESPONSE_TYPE:
    """
    Generate AI response with structured schema output
    """
    agent = Agent(model, output_type=schema)  # type: ignore
    result = await ai_agent_run(
        agent, user_prompt=history.prompt, message_history=history.message_history
    )
    return result.output  # type: ignore


async def new_ai_reply(
        message: Message,
        markup: Optional[ReplyKeyboardMarkup] = None
) -> Message:
    """
    Generate AI reply and send it as a message
    """
    from sophie_bot.modules.ai.utils.ai_chatbot_reply import ai_chatbot_reply

    # Use the existing ai_chatbot_reply implementation but with new history
    return await ai_chatbot_reply(message, None, user_text=None, reply_markup=markup)
