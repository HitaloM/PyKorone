from openai import AsyncOpenAI

from sophie_bot.config import CONFIG

openai_client = AsyncOpenAI(
    api_key=CONFIG.openai_key,
)
