from typing import Any, Optional

from aiogram.types import TelegramObject, User
from aiogram.utils.i18n.middleware import I18nMiddleware

from korone.config import CONFIG
from korone.constants import CACHE_LANGUAGE_TTL_SECONDS
from korone.db.models.chat import ChatModel
from korone.db.models.language import LanguageModel
from korone.logging import get_logger
from korone.utils.cached import cached

logger = get_logger(__name__)


@cached(ttl=CACHE_LANGUAGE_TTL_SECONDS)
async def cache_get_locale_name(chat_id: int) -> Optional[str]:
    locale = await LanguageModel.get_locale(chat_id)

    return locale if locale else None


class LocalizationMiddleware(I18nMiddleware):
    async def get_locale(self, event: TelegramObject, data: dict[str, Any]) -> str:
        chat_in_db: Optional[ChatModel] = data.get("chat_db")

        if not chat_in_db:
            await logger.adebug("LocalizationMiddleware: Chat cannot be found in this event, leaving locale to default")
            return CONFIG.default_locale

        cached_locale = await cache_get_locale_name(chat_in_db.chat_id)
        locale: str = cached_locale if cached_locale else CONFIG.default_locale

        if locale not in self.i18n.available_locales:
            await logger.adebug(
                "LocalizationMiddleware: Locale not available, falling back to default",
                locale=locale,
                available=self.i18n.available_locales,
            )
            locale = CONFIG.default_locale

        if chat_in_db.type == "private":
            user: Optional[User] = getattr(event, "from_user", None)
            user_lang = user.language_code if user else None
            if user_lang and user_lang in self.i18n.available_locales:
                return user_lang

        return CONFIG.default_locale
