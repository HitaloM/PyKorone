from typing import Any, Optional

from aiogram.types import TelegramObject
from aiogram.utils.i18n.middleware import I18nMiddleware

from sophie_bot import CONFIG
from sophie_bot.db.cache.locale import cache_get_locale_name
from sophie_bot.db.models import ChatModel
from sophie_bot.utils.logger import log


class LocalizationMiddleware(I18nMiddleware):
    async def get_locale(self, event: TelegramObject, data: dict[str, Any]) -> str:
        chat_in_db: Optional[ChatModel] = data.get("chat_db")

        if not chat_in_db:
            log.debug("LocalizationMiddleware: Chat cannot be found in this event, leaving locale to default")
            return CONFIG.default_locale

        locale: str = await cache_get_locale_name(chat_in_db.id) or CONFIG.default_locale  # type: ignore
        log.debug("LocalizationMiddleware", chat_id=chat_in_db.id, has_locale=locale)

        return locale
