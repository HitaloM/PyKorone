from typing import TYPE_CHECKING, Any

from aiogram.enums import ChatType
from aiogram.utils.i18n.middleware import SimpleI18nMiddleware

from korone.config import CONFIG
from korone.logger import get_logger
from korone.middlewares.context_data import as_korone_context, get_chat_db

if TYPE_CHECKING:
    from aiogram.types import TelegramObject

logger = get_logger(__name__)


class LocalizationMiddleware(SimpleI18nMiddleware):
    async def get_locale(self, event: TelegramObject, data: dict[str, Any]) -> str:
        chat_in_db = get_chat_db(as_korone_context(data))
        if chat_in_db is None:
            await logger.adebug("LocalizationMiddleware: Chat cannot be found in this event, leaving locale to default")
            return CONFIG.default_locale

        if chat_in_db.language_code:
            if chat_in_db.language_code in self.i18n.available_locales:
                return chat_in_db.language_code
            await logger.adebug(
                "LocalizationMiddleware: Locale not available, falling back to default",
                locale=chat_in_db.language_code,
                available=self.i18n.available_locales,
            )

        if chat_in_db.type == ChatType.PRIVATE:
            return await super().get_locale(event, data)

        return CONFIG.default_locale


class FallbackLocalizationMiddleware(LocalizationMiddleware):
    async def get_locale(self, event: TelegramObject, data: dict[str, Any]) -> str:
        try:
            return await super().get_locale(event, data)
        except Exception:  # ruff: ignore[blind-except]
            await logger.aexception("Could not resolve locale for error reporting")
            return self.i18n.default_locale
