from beanie import PydanticObjectId
from pydantic_ai.models import Model

from sophie_bot.db.models.ai.ai_provider import AIProviderModel
from sophie_bot.modules.ai.utils.ai_models import (
    AI_MODELS,
    DEFAULT_MODELS,
    TRANSLATE_DEFAULT_MODELS,
    AIProviders,
)
from sophie_bot.utils.logger import log


async def get_chat_default_model(chat_id: PydanticObjectId) -> Model:
    provider_name = await AIProviderModel.get_provider_name(chat_id)
    provider_key = provider_name or AIProviders.auto.name
    default_model_name = DEFAULT_MODELS.get(provider_key, DEFAULT_MODELS[AIProviders.auto.name])

    log.debug(f"Default model for chat {chat_id}: {default_model_name}", provider_name=provider_name)

    return AI_MODELS[default_model_name]


async def get_chat_translations_model(chat_id: PydanticObjectId) -> Model:
    provider_name = await AIProviderModel.get_provider_name(chat_id)
    provider_key = provider_name or AIProviders.auto.name
    default_model_name = TRANSLATE_DEFAULT_MODELS.get(provider_key, TRANSLATE_DEFAULT_MODELS[AIProviders.auto.name])

    log.debug(f"Default model for chat {chat_id}: {default_model_name}", provider_name=provider_name)

    return AI_MODELS[default_model_name]
