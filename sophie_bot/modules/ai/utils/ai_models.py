from enum import Enum
from typing import Mapping, Type

from httpx import AsyncClient
from pydantic_ai.models import Model
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.mistral import MistralModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.mistral import MistralProvider
from pydantic_ai.providers.openai import OpenAIProvider

from sophie_bot.config import CONFIG

ai_http_client = AsyncClient(timeout=30)


class AIProviders(str, Enum):
    auto = "auto"
    google = "google"
    mistral = "mistral"
    openai = "openai"


AI_PROVIDERS = {
    AIProviders.google.name: GoogleProvider(api_key=CONFIG.gemini_api_key or ""),
    AIProviders.mistral.name: MistralProvider(api_key=CONFIG.mistral_api_key or ""),
    AIProviders.openai.name: OpenAIProvider(api_key=CONFIG.openai_key or "", http_client=ai_http_client),
}
AI_MODEL_CLASSES = {
    AIProviders.google.name: GoogleProvider,
    AIProviders.mistral.name: MistralModel,
    AIProviders.openai.name: OpenAIModel,
}
AI_PROVIDER_TO_NAME = {
    AIProviders.auto.name: "Auto",
    AIProviders.google.name: "Google Gemini",
    AIProviders.mistral.name: "Mistral AI",
    AIProviders.openai.name: "OpenAI ChatGPT",
}

# Global, ordered list of provider enum names for UI and validation
AVAILABLE_PROVIDER_NAMES: tuple[str, ...] = (
    AIProviders.auto.name,
    AIProviders.openai.name,
    AIProviders.google.name,
    AIProviders.mistral.name,
)


class GoogleModels(Enum):
    gemini_2_5_pro = "gemini-2.5-pro"
    gemini_2_5_flash = "gemini-2.5-flash"


class MistralModels(Enum):
    mistral_large = "mistral-large-latest"
    mistral_small = "mistral-small-latest"
    codestral = "codestral-latest"
    pixtral = "pixtral-12b-2409"


class OpenAIModels(Enum):
    gpt_4o_mini = "gpt-4o-mini"
    gpt_5 = "gpt-5"
    gpt_5_mini = "gpt-5-mini"
    gpt_5_nano = "gpt-5-nano"


AI_PROVIDER_TO_MODEL_CLASS = {
    AIProviders.google.name: GoogleModel,
    AIProviders.mistral.name: MistralModel,
    AIProviders.openai.name: OpenAIModel,
}

PROVIDER_TO_MODELS: Mapping[str, Type[Enum]] = {
    "google": GoogleModels,
    "mistral": MistralModels,
    "openai": OpenAIModels,
}

AI_MODEL_TO_PROVIDER = {
    GoogleModels.gemini_2_5_flash.name: "google",
    GoogleModels.gemini_2_5_pro.name: "google",
    MistralModels.mistral_large.name: "mistral",
    MistralModels.mistral_small.name: "mistral",
    MistralModels.codestral.name: "mistral",
    MistralModels.pixtral.name: "mistral",
    OpenAIModels.gpt_4o_mini.name: "openai",
    OpenAIModels.gpt_5.name: "openai",
    OpenAIModels.gpt_5_mini.name: "openai",
    OpenAIModels.gpt_5_nano.name: "openai",
}

AI_MODEL_TO_SHORT_NAME = {
    GoogleModels.gemini_2_5_flash.value: "Gemini 2.5 Flash",
    GoogleModels.gemini_2_5_pro.value: "Gemini 2.5 Pro",
    MistralModels.mistral_large.value: "Mistral Large",
    MistralModels.mistral_small.value: "Mistral Small",
    MistralModels.codestral.value: "Codestral",
    MistralModels.pixtral.value: "Pixtral 12B",
    OpenAIModels.gpt_4o_mini.value: "GPT-4o mini",
    OpenAIModels.gpt_5.value: "GPT-5",
    OpenAIModels.gpt_5_mini.value: "GPT-5 mini",
    OpenAIModels.gpt_5_nano.value: "GPT-5 nano",
}


def build_models(provider: str, model: str) -> Model:
    # Validate provider → enum mapping
    try:
        model_enum = PROVIDER_TO_MODELS[provider]
    except KeyError:
        raise ValueError(f"Invalid provider: {provider}") from None

    # Validate model name for the provider
    try:
        model_value = model_enum[model].value
    except KeyError:
        raise ValueError(f"Invalid model '{model}' for provider '{provider}'") from None

    # Resolve model class and provider instance
    try:
        ModelClass = AI_PROVIDER_TO_MODEL_CLASS[provider]
        provider_instance = AI_PROVIDERS[provider]
    except KeyError:
        raise ValueError(f"Configuration missing for provider: {provider}") from None

    # Always construct a Model with an associated Provider instance
    return ModelClass(model_value, provider=provider_instance)


AI_MODELS: dict[str, Model] = {
    model_name: build_models(provider, model_name) for model_name, provider in AI_MODEL_TO_PROVIDER.items()
}

DEFAULT_MODELS: dict[str, str] = {
    AIProviders.auto.name: OpenAIModels.gpt_5_mini.name,
    AIProviders.google.name: GoogleModels.gemini_2_5_flash.name,
    AIProviders.mistral.name: MistralModels.mistral_small.name,
    AIProviders.openai.name: OpenAIModels.gpt_5_mini.name,
}

TRANSLATE_DEFAULT_MODELS: dict[str, str] = {
    AIProviders.auto.name: OpenAIModels.gpt_5_nano.name,
    AIProviders.google.name: GoogleModels.gemini_2_5_flash.name,
    AIProviders.mistral.name: MistralModels.mistral_small.name,
    AIProviders.openai.name: OpenAIModels.gpt_5_nano.name,
}
