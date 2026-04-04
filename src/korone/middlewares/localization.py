from typing import TYPE_CHECKING, Any

from aiogram.enums import ChatType
from aiogram.utils.i18n.middleware import I18nMiddleware

from korone.config import CONFIG
from korone.logger import get_logger
from korone.middlewares.context_data import get_chat_db

if TYPE_CHECKING:
    from aiogram.types import TelegramObject, User

logger = get_logger(__name__)


class LocalizationMiddleware(I18nMiddleware):
    async def get_locale(self, event: TelegramObject, data: dict[str, Any]) -> str:
        chat_in_db = get_chat_db(data)
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
            user: User | None = getattr(event, "from_user", None)
            user_lang = user.language_code if user else None
            if user_lang and user_lang in self.i18n.available_locales:
                return user_lang

        return CONFIG.default_locale
