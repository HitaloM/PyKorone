from pydantic_ai import Agent
from pydantic_ai.providers import Provider

from sophie_bot.modules.ai.utils.ai_models import AI_MODELS, GoogleModels, DEFAULT_MODEL


async def new_ai_reply(model: Provider = DEFAULT_MODEL):
    agent = Agent(model)
    result = await agent.run('What does the fox say?')
    print(result.data)