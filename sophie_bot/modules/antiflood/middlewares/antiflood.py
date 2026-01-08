from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.dispatcher.event.bases import CancelHandler
from aiogram.enums import ChatType, ContentType
from aiogram.types import Message, TelegramObject
from babel.support import LazyProxy
from stfu_tg import Doc, Title
from stfu_tg.doc import Element

from sophie_bot.config import CONFIG
from sophie_bot.db.models.antiflood import AntifloodModel
from sophie_bot.db.models.filters import FilterActionType
from sophie_bot.modules.antiflood.config import FLOOD_WINDOW_SECONDS
from sophie_bot.modules.filters.utils_.all_modern_actions import ALL_MODERN_ACTIONS
from sophie_bot.modules.legacy_modules.utils.user_details import is_user_admin
from sophie_bot.services.redis import aredis
from sophie_bot.utils.i18n import gettext as _


class AntifloodMiddleware(BaseMiddleware):
    """Modern antiflood middleware that tracks message counts in configurable windows."""

    FLOOD_WINDOW = FLOOD_WINDOW_SECONDS  # Configurable flood window from module settings
    CACHE_KEY_PREFIX = "antiflood_count"

    @classmethod
    def _get_cache_key(cls, chat_id: int, user_id: int) -> str:
        """Generate cache key for user message count."""
        return f"{cls.CACHE_KEY_PREFIX}:{chat_id}:{user_id}"

    @classmethod
    def _is_message_valid(cls, message: Message) -> bool:
        """Check if message should be counted for antiflood."""
        # Skip service messages
        excluded_types = [ContentType.NEW_CHAT_MEMBERS, ContentType.LEFT_CHAT_MEMBER]
        if message.content_type in excluded_types:
            return False

        # Skip private chats
        if message.chat.type == ChatType.PRIVATE:
            return False

        return True

    async def _increment_message_count(self, chat_id: int, user_id: int) -> int:
        """Increment message count for user and return new count."""
        cache_key = self._get_cache_key(chat_id, user_id)
        new_count = await aredis.incr(cache_key)

        # Set expiry only on first message to ensure consistent window
        if new_count == 1:
            await aredis.expire(cache_key, self.FLOOD_WINDOW)

        return new_count

    async def _reset_flood_count(self, chat_id: int, user_id: int) -> None:
        """Reset flood count for user."""
        cache_key = self._get_cache_key(chat_id, user_id)
        await aredis.delete(cache_key)

    @staticmethod
    async def _apply_action(
        message: Message, data: dict[str, Any], action: FilterActionType
    ) -> tuple[bool, Element | str | LazyProxy | None]:
        """Apply a single configured antiflood action using modern actions."""
        if not message.from_user:
            return False, ""

        modern_action = ALL_MODERN_ACTIONS.get(action.name)
        if not modern_action:
            return False, ""

        result = await modern_action.handle(
            message,
            data,
            action.data or {},
        )
        # Consider the action successful if it returned any text/element
        return (result is not None), result

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Process messages for antiflood detection."""
        if not isinstance(event, Message) or not event.from_user:
            return await handler(event, data)

        chat_id = event.chat.id
        chat_iid = data["connection"].db_model.iid
        user_id = event.from_user.id

        # Check if message should be processed
        if not self._is_message_valid(event):
            return await handler(event, data)

        # Skip admins
        if not CONFIG.debug_mode and await is_user_admin(chat_id, user_id):
            return await handler(event, data)

        # Get antiflood settings (chat_tid is Telegram chat ID)
        antiflood_model = await AntifloodModel.get_by_chat_iid(chat_iid)
        if not antiflood_model.enabled:
            return await handler(event, data)

        # Increment count
        count = await self._increment_message_count(chat_iid, user_id)

        # Check if a threshold exceeded
        if count >= antiflood_model.message_count:
            # Apply all configured actions sequentially
            results: list[Element | str | LazyProxy] = []
            any_success = False
            for action in antiflood_model.actions:
                success, text = await self._apply_action(event, data, action)
                any_success = any_success or success
                if text:
                    results.append(text)

            if any_success:
                # Reset flood count
                await self._reset_flood_count(chat_id, user_id)

                # Delete the triggering message
                await event.delete()

                doc = Doc(
                    Title(_("Flooding detected! 🚫")),
                    _("Triggered by user {user} sending {count} messages in {window} seconds.").format(
                        user=event.from_user.full_name, count=count, window=self.FLOOD_WINDOW
                    ),
                    *results,
                )

                await event.answer(
                    doc.to_html(),
                    disable_web_page_preview=True,
                )

                # Cancel further processing
                raise CancelHandler

        return await handler(event, data)
