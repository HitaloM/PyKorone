from enum import Enum
from typing import Mapping, Type

from httpx import AsyncClient
from pydantic_ai.models import Model
from pydantic_ai.models.mistral import MistralModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.mistral import MistralProvider
from pydantic_ai.providers.openai import OpenAIProvider

from sophie_bot.config import CONFIG

ai_http_client = AsyncClient(timeout=30)


class AIProviders(str, Enum):
    auto = "auto"
    anthropic = "anthropic"
    google = "google"
    mistral = "mistral"
    openai = "openai"


# Configure OpenRouter (OpenAI-compatible) provider for non-Mistral models
_openrouter_provider = OpenAIProvider(
    api_key=CONFIG.openrouter_api_key or "",
    base_url="https://openrouter.ai/api/v1",
    http_client=ai_http_client,
)

AI_PROVIDERS = {
    AIProviders.anthropic.name: _openrouter_provider,
    AIProviders.google.name: _openrouter_provider,
    AIProviders.mistral.name: MistralProvider(api_key=CONFIG.mistral_api_key or ""),
    AIProviders.openai.name: _openrouter_provider,
}
AI_MODEL_CLASSES = {
    AIProviders.anthropic.name: OpenAIProvider,
    AIProviders.google.name: OpenAIProvider,
    AIProviders.mistral.name: MistralModel,
    AIProviders.openai.name: OpenAIProvider,
}
AI_PROVIDER_TO_NAME = {
    AIProviders.auto.name: "Auto",
    AIProviders.anthropic.name: "Anthropic Claude",
    AIProviders.google.name: "Google Gemini",
    AIProviders.mistral.name: "Mistral AI",
    AIProviders.openai.name: "OpenAI ChatGPT",
}

# Global, ordered list of provider enum names for UI and validation
AVAILABLE_PROVIDER_NAMES: tuple[str, ...] = (
    AIProviders.auto.name,
    AIProviders.anthropic.name,
    AIProviders.openai.name,
    AIProviders.google.name,
    AIProviders.mistral.name,
)


class GoogleModels(Enum):
    # OpenRouter slugs for Google models
    gemini_2_5_pro = "google/gemini-2.5-pro"
    gemini_2_5_flash = "google/gemini-2.5-flash"


class AnthropicModels(Enum):
    # OpenRouter slugs for Anthropic models
    sonnet_4_5 = "anthropic/claude-sonnet-4.5"
    haiku_4_5 = "anthropic/claude-4.5-haiku"
    haiku_3_5 = "anthropic/claude-3.5-haiku"


class MistralModels(Enum):
    mistral_large = "mistral-large-latest"
    mistral_medium = "mistral-medium-latest"
    mistral_small = "mistral-small-latest"
    magistral_small = "magistral-small-latest"
    magistral_medium = "magistral-medium-latest"
    codestral = "codestral-latest"
    pixtral = "pixtral-12b-2409"


class OpenAIModels(Enum):
    # OpenRouter slugs for OpenAI models
    gpt_4o_mini = "openai/gpt-4o-mini"
    gpt_5 = "openai/gpt-5"
    gpt_5_mini = "openai/gpt-5-mini"
    gpt_5_nano = "openai/gpt-5-nano"


AI_PROVIDER_TO_MODEL_CLASS = {
    AIProviders.anthropic.name: OpenAIChatModel,
    AIProviders.google.name: OpenAIChatModel,
    AIProviders.mistral.name: MistralModel,
    AIProviders.openai.name: OpenAIChatModel,
}

PROVIDER_TO_MODELS: Mapping[str, Type[Enum]] = {
    "anthropic": AnthropicModels,
    "google": GoogleModels,
    "mistral": MistralModels,
    "openai": OpenAIModels,
}

AI_MODEL_TO_PROVIDER = {
    AnthropicModels.sonnet_4_5.name: "anthropic",
    AnthropicModels.haiku_4_5.name: "anthropic",
    AnthropicModels.haiku_3_5.name: "anthropic",
    GoogleModels.gemini_2_5_flash.name: "google",
    GoogleModels.gemini_2_5_pro.name: "google",
    MistralModels.mistral_large.name: "mistral",
    MistralModels.mistral_medium.name: "mistral",
    MistralModels.mistral_small.name: "mistral",
    MistralModels.codestral.name: "mistral",
    MistralModels.pixtral.name: "mistral",
    MistralModels.magistral_small.name: "mistral",
    MistralModels.magistral_medium.name: "mistral",
    OpenAIModels.gpt_4o_mini.name: "openai",
    OpenAIModels.gpt_5.name: "openai",
    OpenAIModels.gpt_5_mini.name: "openai",
    OpenAIModels.gpt_5_nano.name: "openai",
}

AI_MODEL_TO_SHORT_NAME = {
    AnthropicModels.sonnet_4_5.value: "Claude Sonnet 4.5",
    AnthropicModels.haiku_4_5.value: "Claude Haiku 4.5",
    AnthropicModels.haiku_3_5.value: "Claude Haiku 3.5",
    GoogleModels.gemini_2_5_flash.value: "Gemini 2.5 Flash",
    GoogleModels.gemini_2_5_pro.value: "Gemini 2.5 Pro",
    MistralModels.mistral_large.value: "Mistral Large",
    MistralModels.mistral_medium.value: "Mistral Medium",
    MistralModels.mistral_small.value: "Mistral Small",
    MistralModels.codestral.value: "Codestral",
    MistralModels.pixtral.value: "Pixtral 12B",
    MistralModels.magistral_small.value: "Magistral Small",
    MistralModels.magistral_medium.value: "Magistral Medium",
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
    AIProviders.auto.name: MistralModels.mistral_small.name,
    AIProviders.anthropic.name: AnthropicModels.haiku_4_5.name,
    AIProviders.google.name: GoogleModels.gemini_2_5_flash.name,
    AIProviders.mistral.name: MistralModels.mistral_small.name,
    AIProviders.openai.name: OpenAIModels.gpt_5_mini.name,
}

TRANSLATE_DEFAULT_MODELS: dict[str, str] = {
    AIProviders.auto.name: MistralModels.magistral_medium.name,
    AIProviders.anthropic.name: AnthropicModels.haiku_4_5.name,
    AIProviders.google.name: GoogleModels.gemini_2_5_flash.name,
    AIProviders.mistral.name: MistralModels.magistral_medium.name,
    AIProviders.openai.name: OpenAIModels.gpt_5_nano.name,
}
