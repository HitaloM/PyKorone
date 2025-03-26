from pydantic_ai import Agent
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool
from pydantic_ai.messages import ModelRequest
from pydantic_ai.providers import Provider

from sophie_bot.modules.ai.utils.ai_agent_run import ai_agent_run, AIAgentResult
from sophie_bot.modules.ai.utils.ai_models import DEFAULT_PROVIDER


async def new_ai_generate(
        user_prompt: str,
        history: list[ModelRequest],
        model: Provider = DEFAULT_PROVIDER,
) -> AIAgentResult:
    """
    Used to generate the AI Chat-bot result text
    """
    agent = Agent(
        model,
        tools=[duckduckgo_search_tool()]
    )
    result = await ai_agent_run(
        agent,
        user_prompt=user_prompt,
        message_history=history
    )
    return result
