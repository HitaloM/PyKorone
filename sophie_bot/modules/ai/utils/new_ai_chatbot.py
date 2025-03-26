from pydantic_ai import Agent
from pydantic_ai.providers import Provider

from sophie_bot.modules.ai.utils.ai_agent_run import ai_agent_run, AIAgentResult
from sophie_bot.modules.ai.utils.ai_models import DEFAULT_PROVIDER
from sophie_bot.modules.ai.utils.new_message_history import NewAIMessageHistory


async def new_ai_generate(
        history: NewAIMessageHistory,
        model: Provider = DEFAULT_PROVIDER,
        agent_kwargs=None,
        **kwargs
) -> AIAgentResult:
    """
    Used to generate the AI Chat-bot result text
    """
    if agent_kwargs is None:
        agent_kwargs = dict()

    agent = Agent(
        model,
        **kwargs
    )
    result = await ai_agent_run(
        agent,
        user_prompt=history.prompt,
        message_history=history.message_history,
        **agent_kwargs
    )
    return result
