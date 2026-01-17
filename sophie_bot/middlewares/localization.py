from typing import Any, Optional

from aiogram.types import TelegramObject, User
from aiogram.utils.i18n.middleware import I18nMiddleware

from sophie_bot.config import CONFIG
from sophie_bot.db.models import ChatModel
from sophie_bot.utils.logger import log


class LocalizationMiddleware(I18nMiddleware):
    async def get_locale(self, event: TelegramObject, data: dict[str, Any]) -> str:
        chat_in_db: Optional[ChatModel] = data.get("chat_db")

        if not chat_in_db:
            log.debug("LocalizationMiddleware: Chat cannot be found in this event, leaving locale to default")
            return CONFIG.default_locale

        if chat_in_db.language_code:
            return chat_in_db.language_code

        # Fallback to user language if in private chat
        if chat_in_db.type == "private":
            user: Optional[User] = getattr(event, "from_user", None)
            user_lang = user.language_code if user else None
            if user_lang and user_lang in self.i18n.available_locales:
                return user_lang

        return CONFIG.default_locale
