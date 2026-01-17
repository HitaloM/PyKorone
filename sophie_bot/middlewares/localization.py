from typing import Any, Optional

from aiogram.types import TelegramObject
from aiogram.utils.i18n.middleware import I18nMiddleware

from sophie_bot.config import CONFIG
from sophie_bot.db.models import ChatModel
from sophie_bot.modules.legacy_modules.utils.language import get_chat_lang
from sophie_bot.utils.logger import log


class LocalizationMiddleware(I18nMiddleware):
    @staticmethod
    async def get_legacy_locale(chat_id: int):
        return await get_chat_lang(chat_id)

    async def get_locale(self, event: TelegramObject, data: dict[str, Any]) -> str:
        chat_in_db: Optional[ChatModel] = data.get("chat_db")

        if not chat_in_db:
            log.debug("LocalizationMiddleware: Chat cannot be found in this event, leaving locale to default")
            return CONFIG.default_locale

        # locale: str = await cache_get_locale_name(chat_in_db.id) or CONFIG.default_locale

        locale: str = await self.get_legacy_locale(chat_in_db.tid) or CONFIG.default_locale

        log.debug("LocalizationMiddleware", chat_id=chat_in_db.iid, has_locale=locale)

        return locale
