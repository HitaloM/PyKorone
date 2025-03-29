from enum import Enum

from httpx import AsyncClient
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers import Provider
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from pydantic_ai.providers.openai import OpenAIProvider

from sophie_bot.config import CONFIG

ai_http_client = AsyncClient(timeout=30)


class AIProviders(str, Enum):
    google = "google"
    openai = "openai"


AI_PROVIDERS = {
    AIProviders.google.name: GoogleGLAProvider(api_key=CONFIG.gemini_api_key, http_client=ai_http_client),
    AIProviders.openai.name: OpenAIProvider(api_key=CONFIG.openai_key, http_client=ai_http_client),
}
AI_MODEL_CLASSES = {AIProviders.google.name: GeminiModel, AIProviders.openai.name: OpenAIModel}
AI_PROVIDER_TO_NAME = {AIProviders.google.name: "Google Gemini", AIProviders.openai.name: "OpenAI (ChatGPT)"}


class GoogleModels(Enum):
    gemini_2_0_flash = "gemini-2.0-flash"
    gemini_2_5_pro = "gemini-2.5-pro-exp-03-25"


class OpenAIModels(Enum):
    o3_mini = "o3-mini"
    gpt_4o = "gpt-4o"
    gpt_4o_mini = "gpt-4o-mini"


AI_MODEL_TO_PROVIDER = {
    GoogleModels.gemini_2_0_flash.name: "google",
    GoogleModels.gemini_2_5_pro.name: "google",
    OpenAIModels.o3_mini.name: "openai",
    OpenAIModels.gpt_4o.name: "openai",
    OpenAIModels.gpt_4o_mini.name: "openai",
}

AI_MODEL_TO_SHORT_NAME = {
    GoogleModels.gemini_2_0_flash.value: "Gemini 2.0 Flash",
    GoogleModels.gemini_2_5_pro.value: "Gemini 2.5 Pro (Experimental)",
    OpenAIModels.o3_mini.value: "o3 mini",
    OpenAIModels.gpt_4o.value: "GPT-4o",
    OpenAIModels.gpt_4o_mini.value: "GTP-4o mini",
}


def build_models(provider: str, model: str) -> Provider:
    if provider not in AI_MODEL_CLASSES:
        raise ValueError(f"Invalid provider: {provider}")

    # Validate model for provider
    valid_models = GoogleModels if provider == "google" else OpenAIModels
    try:
        model_value = valid_models[model].value
    except KeyError:
        raise ValueError(f"Invalid model '{model}' for provider '{provider}'")

    ModelClass = AI_MODEL_CLASSES[provider]
    return ModelClass(model_value, provider=AI_PROVIDERS[provider])


AI_MODELS: dict[str, Provider] = {
    model_name: build_models(provider, model_name) for model_name, provider in AI_MODEL_TO_PROVIDER.items()
}

DEFAULT_PROVIDER: Provider = AI_MODELS[GoogleModels.gemini_2_0_flash.name]
