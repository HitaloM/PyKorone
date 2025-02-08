from openai import AsyncOpenAI

from sophie_bot import CONFIG

openai_client = AsyncOpenAI(
    api_key=CONFIG.openai_key,
)
