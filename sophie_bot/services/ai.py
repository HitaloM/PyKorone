from openai import AsyncOpenAI

from sophie_bot import CONFIG

ai_client = AsyncOpenAI(
    api_key=CONFIG.openai_key,
)
