from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from fast_langdetect import detect

from sophie_bot import CONFIG
from sophie_bot.db.models import AIAutotranslateModel, ChatModel
from sophie_bot.db.models.chat import ChatType
from sophie_bot.modules.ai.handlers.translate import AiTranslate
from sophie_bot.utils.logger import log


class AiAutoTranslateMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        chat_db: Optional[ChatModel] = data.get("chat_db", None)
        chat_lang: str = data["i18n"].current_locale

        result = await handler(event, data)

        if (
            chat_db
            and chat_db.type != ChatType.private
            and data.get("ai_enabled")
            and isinstance(event, Message)
            and await AIAutotranslateModel.get_state(chat_db.id)
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

            text_to_detect = data["text"].replace("\n", "").lower()
            detected_lang = detect(text_to_detect, low_memory=CONFIG.ai_autotrans_lowmem)
            log.debug("AiAutoTranslateMiddleware: Detected language", chat_lang=chat_lang, lang=detected_lang)

            if (not chat_lang.startswith(detected_lang["lang"]) and detected_lang["score"] >= 0.3) or data.get("voice"):
                log.debug("AiAutoTranslateMiddleware: Translating...")
                await AiTranslate(event, **data)

        return result
