from typing import TYPE_CHECKING

from aiogram.types import TelegramObject
from aiogram.utils.i18n.middleware import I18nMiddleware

from korone.config import CONFIG
from korone.constants import CACHE_LANGUAGE_TTL_SECONDS
from korone.db.models.chat import ChatModel
from korone.db.repositories.language import LanguageRepository
from korone.logger import get_logger
from korone.utils.cached import Cached

if TYPE_CHECKING:
    from aiogram.types import User

logger = get_logger(__name__)

type MiddlewareDataValue = (
    str | int | float | bool | TelegramObject | ChatModel | dict[str, str | int | float | bool | None] | None
)
type MiddlewareData = dict[str, MiddlewareDataValue]


@Cached(ttl=CACHE_LANGUAGE_TTL_SECONDS)
async def cache_get_locale_name(chat_id: int) -> str | None:
    locale = await LanguageRepository.get_locale(chat_id)

    return locale or None


class LocalizationMiddleware(I18nMiddleware):
    async def get_locale(self, event: TelegramObject, data: MiddlewareData) -> str:
        chat_in_db = data.get("chat_db")
        if not isinstance(chat_in_db, ChatModel):
            await logger.adebug("LocalizationMiddleware: Chat cannot be found in this event, leaving locale to default")
            return CONFIG.default_locale

        cached_locale = await cache_get_locale_name(chat_in_db.chat_id)
        locale: str = cached_locale or CONFIG.default_locale

        if locale not in self.i18n.available_locales:
            await logger.adebug(
                "LocalizationMiddleware: Locale not available, falling back to default",
                locale=locale,
                available=self.i18n.available_locales,
            )
            locale = CONFIG.default_locale

        if chat_in_db.type == "private":
            user: User | None = getattr(event, "from_user", None)
            user_lang = user.language_code if user else None
            if user_lang and user_lang in self.i18n.available_locales:
                return user_lang

        return CONFIG.default_locale
