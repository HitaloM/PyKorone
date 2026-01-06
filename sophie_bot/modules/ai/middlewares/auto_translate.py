from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from sophie_bot.db.models import AIAutotranslateModel, ChatModel
from sophie_bot.db.models.chat import ChatType
from sophie_bot.modules.ai.handlers.translate import AiTranslate
from sophie_bot.modules.ai.utils.detect_lang import (
    is_text_language,
    lang_code_to_language,
)
from sophie_bot.utils.feature_flags import is_enabled
from sophie_bot.utils.i18n import I18nNew
from sophie_bot.utils.logger import log


class AiAutoTranslateMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        chat_db: Optional[ChatModel] = data.get("chat_db", None)
        i18n: I18nNew = data["i18n"]

        result = await handler(event, data)

        if not await is_enabled("ai_translations"):
            return result

        if (
            chat_db
            and chat_db.type != ChatType.private
            and data.get("ai_enabled")
            and isinstance(event, Message)
            and await AIAutotranslateModel.get_state(chat_db.iid)
        ):
            data["autotranslate"] = True
            data["text"] = event.text or event.caption or ""
            data["voice"] = event.voice

            # Some checks to prevent unnecessary translations
            if not data["voice"]:
                if not data["text"]:
                    return result
                elif data["text"].startswith("http") or data["text"].startswith("/"):
                    log.debug("AiAutoTranslateMiddleware: Ignoring non-text message")
                    return result
                elif len(data["text"]) <= 5:
                    log.debug("AiAutoTranslateMiddleware: Ignoring short message")
                    return result

            text_to_detect = data["text"].lower()

            data["silent_error"] = True

            if data.get("voice"):
                log.debug("AiAutoTranslateMiddleware: Voice message - Translating anyway!")
                await AiTranslate(event, **data)

            # Detect language
            if not is_text_language(text_to_detect, lang_code_to_language(i18n.current_locale_iso_639_1)):
                log.debug("AiAutoTranslateMiddleware: Detected another language, translating!")
                await AiTranslate(event, **data)

        return result
