from __future__ import annotations

from openai import AsyncOpenAI
from mistralai import Mistral

from sophie_bot.config import CONFIG

openai_client = AsyncOpenAI(
    api_key=CONFIG.openrouter_api_key,
    base_url="https://openrouter.ai/api/v1",
)

mistral_client = Mistral(api_key=CONFIG.mistral_api_key or "")
