from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.types import Message, TelegramObject
from mistralai import SDKError
from stfu_tg import Doc, KeyValue, Section, Title, UserLink, VList

from sophie_bot.config import CONFIG
from sophie_bot.db.models import AIModeratorModel, ChatModel
from sophie_bot.db.models.chat import ChatType
from sophie_bot.modules.ai.utils.ai_moderator import (
    MODERATION_CATEGORIES_TRANSLATES,
    check_moderator,
)
from sophie_bot.modules.error.utils.capture import capture_sentry
from sophie_bot.modules.legacy_modules.utils.user_details import is_user_admin
from sophie_bot.services.bot import bot
from sophie_bot.utils.feature_flags import is_enabled
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import ngettext as pl_
from sophie_bot.utils.logger import log


class AiModeratorMiddleware(BaseMiddleware):
    @staticmethod
    async def _triggered(message: Message, categories: dict):
        await message.delete()

        triggered_categories: dict = {key: triggered for key, triggered in categories.items() if triggered}

        doc = Doc(
            Title(_("✋ AI Moderator")),
            _("This message violates the AI moderator policy and therefore has been deleted."),
            KeyValue(_("Message author"), UserLink(message.from_user.id, message.from_user.first_name)),  # type: ignore
            Section(
                VList(
                    *(
                        MODERATION_CATEGORIES_TRANSLATES[key] if key in MODERATION_CATEGORIES_TRANSLATES else key
                        for key in triggered_categories.keys()
                    ),
                    prefix="- " if len(triggered_categories) > 1 else "",
                ),
                title=pl_("Reason", "Reasons", len(triggered_categories)),
            ),
        )
        await bot.send_message(message.chat.id, text=doc.to_html(), message_thread_id=message.message_thread_id)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        chat_db: Optional[ChatModel] = data.get("chat_db", None)
        log.debug("AiModeratorMiddleware: checking moderator...")

        # Global kill-switch: AI Moderation
        if not await is_enabled("ai_moderation"):
            return await handler(event, data)

        if chat_db and chat_db.type != ChatType.private and data.get("ai_enabled") and isinstance(event, Message):
            settings = await AIModeratorModel.find_one(AIModeratorModel.chat.id == chat_db.iid)
            if not settings or not settings.enabled:
                return await handler(event, data)

            if not (event.text or event.caption or event.photo or event.audio):
                return await handler(event, data)

            if not event.from_user:
                return await handler(event, data)

            if not CONFIG.debug_mode and await is_user_admin(chat_db.tid, event.from_user.id):
                return await handler(event, data)

            try:
                result = await check_moderator(event, settings=settings)
                if result.flagged:
                    await self._triggered(event, result.categories.to_dict())
                    raise SkipHandler
            except SDKError as err:
                capture_sentry(err)

        return await handler(event, data)
