from __future__ import annotations

import httpx
from openai import AsyncOpenAI
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from .settings import VulcanAPISettings
from .transport import VulcanOpenAITransport

_OPENAI_PROXY_BASE_URL = "https://openai-proxy.local/v1"
_VULCAN_API_SETTINGS = VulcanAPISettings()
_OPENAI_PROVIDER: OpenAIProvider | None = None


def _get_openai_provider() -> OpenAIProvider:
    global _OPENAI_PROVIDER  # noqa: PLW0603
    if _OPENAI_PROVIDER is None:
        # NOTE: AsyncOpenAI/OpenAIProvider is built on top of httpx and expects an
        # httpx-compatible client. We keep httpx only at this boundary layer.
        # Actual upstream HTTP calls to Vulcan are executed via the global aiohttp
        # session inside VulcanOpenAITransport/TokenManager.
        transport = VulcanOpenAITransport(_VULCAN_API_SETTINGS)
        http_client = httpx.AsyncClient(
            transport=transport, timeout=httpx.Timeout(60.0), base_url=_OPENAI_PROXY_BASE_URL
        )
        openai_client = AsyncOpenAI(api_key="vulcan-proxy", base_url=_OPENAI_PROXY_BASE_URL, http_client=http_client)
        _OPENAI_PROVIDER = OpenAIProvider(openai_client=openai_client)

    return _OPENAI_PROVIDER


def get_vulcan_openai_chat_model() -> OpenAIChatModel:
    model_name = _VULCAN_API_SETTINGS.default_model
    return OpenAIChatModel(model_name=model_name, provider=_get_openai_provider())
