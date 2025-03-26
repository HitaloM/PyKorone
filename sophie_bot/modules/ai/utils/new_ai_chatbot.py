from pydantic_ai import Agent
from pydantic_ai.messages import ModelRequest
from pydantic_ai.providers import Provider
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.modules.ai.utils.ai_models import AI_MODELS, GoogleModels, DEFAULT_MODEL


async def new_ai_reply(
        user_prompt: str,
        history: list[ModelRequest],
        model: Provider = DEFAULT_MODEL,
) -> str:
    """
    Used to generate the AI Chat-bot result text
    """
    agent = Agent(model)
    result = await agent.run(
        user_prompt,
        message_history=history
    )
    return result.data or _("No text from the AI Model")
