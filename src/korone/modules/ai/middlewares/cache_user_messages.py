from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware
from aiogram.enums import ChatType
from aiogram.types import Message

from korone.config import CONFIG
from korone.logger import get_logger
from korone.modules.ai.filters.ai_enabled import AIEnabledFilter
from korone.modules.ai.fsm.pm import AI_PM_RESET, AI_PM_STOP_TEXT, AiPMFSM
from korone.modules.ai.utils.cache_messages import cache_message
from korone.modules.ai.utils.self_reply import is_ai_message

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from aiogram.fsm.context import FSMContext
    from aiogram.types import TelegramObject

    from korone.db.models.chat import ChatModel

logger = get_logger(__name__)


def _extract_command_name(text: str) -> str | None:
    stripped = text.strip()
    if not stripped:
        return None

    if stripped[0] not in CONFIG.commands_prefix:
        return None

    return stripped[1:].split(maxsplit=1)[0].split("@", maxsplit=1)[0].lower()


def _has_command_argument(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False

    command_parts = stripped[1:].split(maxsplit=1)
    return len(command_parts) > 1 and bool(command_parts[1].strip())


def _is_ai_reply_message(message: Message) -> bool:
    reply = message.reply_to_message
    if not reply:
        return False

    if reply.from_user and reply.from_user.id != CONFIG.bot_id:
        return False

    return is_ai_message(reply.text or reply.caption or "")


def _is_ai_control_text(text: str) -> bool:
    return text.strip() in {str(AI_PM_STOP_TEXT), str(AI_PM_RESET)}


class CacheUserMessagesMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[object]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> object:
        chat_db = data.get("chat_db")
        ai_enabled = await self._resolve_ai_enabled(event, chat_db)
        data["ai_enabled"] = ai_enabled

        result = await handler(event, data)

        if not isinstance(event, Message) or not chat_db or not event.from_user:
            return result

        if not ai_enabled:
            return result

        text = (event.text or event.caption or "").strip()
        if not text:
            return result

        in_pm_ai_mode = await self._is_pm_ai_mode(data.get("state"))
        if not self._should_cache_message(event, text=text, in_pm_ai_mode=in_pm_ai_mode):
            return result

        await cache_message(
            text, chat_id=chat_db.chat_id, user_id=event.from_user.id, role="user", name=event.from_user.full_name
        )
        return result

    @staticmethod
    async def _resolve_ai_enabled(event: TelegramObject, chat_db: ChatModel | None) -> bool:
        if isinstance(event, Message) and event.chat.type == ChatType.PRIVATE:
            return True

        if chat_db is None:
            return False

        return await AIEnabledFilter.get_status(chat_db)

    @staticmethod
    async def _is_pm_ai_mode(state: FSMContext | None) -> bool:
        if state is None:
            return False

        current_state = await state.get_state()
        return current_state == AiPMFSM.in_ai.state

    @staticmethod
    def _should_cache_message(message: Message, *, text: str, in_pm_ai_mode: bool) -> bool:
        if _is_ai_control_text(text):
            logger.debug("CacheUserMessagesMiddleware: skipping AI control text")
            return False

        command_name = _extract_command_name(text)
        if command_name:
            if command_name == "aireset":
                logger.debug("CacheUserMessagesMiddleware: skipping reset command")
                return False

            if message.chat.type == ChatType.PRIVATE:
                # PM uses /ai to enter mode, so command lines are usually not useful context.
                return False

            return command_name == "ai" and _has_command_argument(text)

        if message.chat.type == ChatType.PRIVATE:
            return in_pm_ai_mode

        return _is_ai_reply_message(message)
