from enum import Enum

from httpx import AsyncClient
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers import Provider
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from pydantic_ai.providers.openai import OpenAIProvider

from sophie_bot.config import CONFIG

ai_http_client = AsyncClient(timeout=30)
AI_PROVIDERS = {
    'google': GoogleGLAProvider(api_key=CONFIG.gemini_api_key, http_client=ai_http_client),
    'openai': OpenAIProvider(api_key=CONFIG.openai_key, http_client=ai_http_client)
}
AI_MODEL_CLASSES = {
    'google': GeminiModel,
    'openai': OpenAIModel
}

class GoogleModels(Enum):
    gemini_1_5_flash = "gemini-1.5-flash"

class OpenAIModels(Enum):
    gpt_4 = "gpt-4"

AI_MODEL_TO_PROVIDER = {
    'gemini_1_5_flash': 'google',
    'gpt_4': 'openai',
}

def build_models(provider: str, model: str) -> Provider:
    if provider not in AI_MODEL_CLASSES:
        raise ValueError(f"Invalid provider: {provider}")

    # Validate model for provider
    valid_models = GoogleModels if provider == 'google' else OpenAIModels
    try:
        model_value = valid_models[model].value
    except KeyError:
        raise ValueError(f"Invalid model '{model}' for provider '{provider}'")

    ModelClass = AI_MODEL_CLASSES[provider]
    return ModelClass(model_value, provider=AI_PROVIDERS[provider])


AI_MODELS: dict[str, Provider] = {
    model_name: build_models(
        provider, model_name
    ) for model_name, provider in AI_MODEL_TO_PROVIDER.items()
}

DEFAULT_MODEL = AI_MODELS[GoogleModels.gemini_1_5_flash.name]
