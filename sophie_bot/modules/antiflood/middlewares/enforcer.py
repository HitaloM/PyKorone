from __future__ import annotations

from typing import Any, Awaitable, Callable, Optional

from aiogram import BaseMiddleware
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.enums import ChatType, ContentType
from aiogram.types import Message, TelegramObject
from stfu_tg import Doc, KeyValue, Title, UserLink

from sophie_bot.db.models import ChatModel
from sophie_bot.db.models.antiflood import AntifloodModel
from sophie_bot.modules.legacy_modules.utils.restrictions import (
    ban_user,
    kick_user,
    mute_user,
)
from sophie_bot.modules.legacy_modules.utils.user_details import is_user_admin
from sophie_bot.services.redis import aredis
from sophie_bot.utils.feature_flags import is_enabled
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.logger import log

# Redis key patterns
FLOOD_COUNT_KEY = "antiflood:count:{chat_id}:{user_id}"
FLOOD_STATE_KEY = "antiflood:state:{chat_id}"

# Default flood window in seconds
FLOOD_WINDOW_SECONDS = 30


class AntifloodEnforcerMiddleware(BaseMiddleware):
    """Middleware that enforces antiflood protection in group chats."""

    @staticmethod
    def _is_message_valid(message: Message) -> bool:
        """Check if this message type should be tracked for flood detection."""
        excluded_types = {ContentType.NEW_CHAT_MEMBERS, ContentType.LEFT_CHAT_MEMBER}
        if message.content_type in excluded_types:
            return False
        if message.chat.type == ChatType.PRIVATE:
            return False
        if not message.from_user:
            return False
        return True

    @staticmethod
    def _get_count_key(chat_id: int, user_id: int) -> str:
        """Get Redis key for user's message count."""
        return FLOOD_COUNT_KEY.format(chat_id=chat_id, user_id=user_id)

    @staticmethod
    def _get_state_key(chat_id: int) -> str:
        """Get Redis key for last user who sent a message in the chat."""
        return FLOOD_STATE_KEY.format(chat_id=chat_id)

    async def _get_flood_count(self, chat_id: int, user_id: int) -> int:
        """Get current message count for user in chat."""
        key = self._get_count_key(chat_id, user_id)
        count = await aredis.get(key)
        return int(count) if count else 0

    async def _increment_flood_count(self, chat_id: int, user_id: int) -> int:
        """Increment and return user's message count."""
        key = self._get_count_key(chat_id, user_id)
        count = await aredis.incr(key)
        # Set expiration on first increment
        if count == 1:
            await aredis.expire(key, FLOOD_WINDOW_SECONDS)
        return int(count)

    async def _reset_flood_count(self, chat_id: int, user_id: int) -> None:
        """Reset user's message count."""
        key = self._get_count_key(chat_id, user_id)
        await aredis.delete(key)

    async def _get_last_user(self, chat_id: int) -> Optional[int]:
        """Get ID of last user who sent a message in the chat."""
        key = self._get_state_key(chat_id)
        user_id = await aredis.get(key)
        return int(user_id) if user_id else None

    async def _set_last_user(self, chat_id: int, user_id: int) -> None:
        """Set the last user who sent a message in the chat."""
        key = self._get_state_key(chat_id)
        await aredis.set(key, user_id)

    async def _execute_action(self, message: Message, settings: AntifloodModel) -> bool:
        """Execute the configured antiflood action. Returns True if action succeeded."""
        chat_id = message.chat.id
        user_id = message.from_user.id  # type: ignore[union-attr]

        # Get action from settings (use first action or default to ban)
        action_name = "ban_user"
        if settings.actions:
            action_name = settings.actions[0].name
        elif settings.action:
            # Legacy action mapping
            action_map = {"ban": "ban_user", "kick": "kick_user", "mute": "mute_user"}
            action_name = action_map.get(settings.action, "ban_user")

        log.info(f"Antiflood triggered: executing {action_name} on user {user_id} in chat {chat_id}")

        if action_name == "ban_user":
            return await ban_user(chat_id, user_id)
        elif action_name == "kick_user":
            return await kick_user(chat_id, user_id)
        elif action_name == "mute_user":
            return await mute_user(chat_id, user_id)
        else:
            log.warning(f"Unknown antiflood action: {action_name}")
            return False

    def _get_action_text(self, settings: AntifloodModel) -> str:
        """Get human-readable action text."""
        action_name = "ban_user"
        if settings.actions:
            action_name = settings.actions[0].name
        elif settings.action:
            action_map = {"ban": "ban_user", "kick": "kick_user", "mute": "mute_user"}
            action_name = action_map.get(settings.action, "ban_user")

        action_texts = {
            "ban_user": _("Banned"),
            "kick_user": _("Kicked"),
            "mute_user": _("Muted"),
        }
        return action_texts.get(action_name, _("Restricted"))

    async def _handle_flood(self, message: Message, settings: AntifloodModel) -> None:
        """Handle flood violation: execute action and notify."""
        user_id = message.from_user.id  # type: ignore[union-attr]
        first_name = message.from_user.first_name  # type: ignore[union-attr]

        # Try to delete the flooding message
        try:
            await message.delete()
        except Exception:
            pass

        # Execute action
        success = await self._execute_action(message, settings)
        if not success:
            return

        # Reset flood count after action
        await self._reset_flood_count(message.chat.id, user_id)

        # Notify the chat
        action_text = self._get_action_text(settings)
        doc = Doc(
            Title(_("⚠️ Antiflood")),
            _("User has been restricted for flooding."),
            KeyValue(_("User"), UserLink(user_id, first_name)),
            KeyValue(_("Action"), action_text),
        )
        await message.answer(doc.to_html())

    async def _check_and_enforce(self, message: Message, settings: AntifloodModel) -> bool:
        """
        Check flood state and enforce if limit exceeded.
        Returns True if flood was triggered and message should be skipped.
        """
        chat_id = message.chat.id
        user_id = message.from_user.id  # type: ignore[union-attr]

        # Get last user who sent a message
        last_user = await self._get_last_user(chat_id)

        # If different user, reset count for current user
        if last_user != user_id:
            await self._reset_flood_count(chat_id, user_id)
            await self._set_last_user(chat_id, user_id)
            await self._increment_flood_count(chat_id, user_id)
            return False

        # Same user - increment and check
        count = await self._increment_flood_count(chat_id, user_id)

        if count >= settings.message_count:
            await self._handle_flood(message, settings)
            return True

        return False

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        message: Message = event
        log.debug(f"AntifloodEnforcerMiddleware: checking message from {message.from_user}")

        # Check global kill switch
        if not await is_enabled("antiflood"):
            return await handler(event, data)

        # Check if message should be tracked
        if not self._is_message_valid(message):
            return await handler(event, data)

        # Get chat from database
        chat_db: Optional[ChatModel] = data.get("chat_db")
        if not chat_db:
            chat_db = await ChatModel.get_by_tid(message.chat.id)
            if not chat_db:
                return await handler(event, data)

        # Get antiflood settings for this chat
        settings = await AntifloodModel.find_one(AntifloodModel.chat.id == chat_db.iid)
        if not settings or not settings.enabled:
            return await handler(event, data)

        # Skip admins
        if await is_user_admin(message.chat.id, message.from_user.id):  # type: ignore[union-attr]
            await self._set_last_user(message.chat.id, message.from_user.id)  # type: ignore[union-attr]
            return await handler(event, data)

        # Check and enforce flood
        if await self._check_and_enforce(message, settings):
            raise SkipHandler

        return await handler(event, data)
