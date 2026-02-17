from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware
from aiogram.types import Update

from korone.constants import CACHE_ADMIN_TTL_SECONDS
from korone.db.repositories.chat_admin import ChatAdminRepository
from korone.logger import get_logger
from korone.modules.utils_.chat_member import update_chat_members

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from aiogram.types import TelegramObject

    from korone.db.models.chat import ChatModel
    from korone.db.models.chat_admin import ChatAdminModel

logger = get_logger(__name__)


class AdminCacheMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Update):
            return await handler(event, data)

        await self._refresh_cache_if_needed(data)
        return await handler(event, data)

    async def _refresh_cache_if_needed(self, data: dict[str, Any]) -> None:
        chat_db = data.get("group_db") or data.get("chat_db")
        if chat_db is None:
            logger.debug("AdminCacheMiddleware: no chat model available, skipping")
            return

        chat_tid = getattr(chat_db, "chat_id", None)
        if not isinstance(chat_tid, int) or chat_tid > 0:
            logger.debug("AdminCacheMiddleware: not a group chat, skipping", chat_id=chat_tid)
            return

        if await self._is_cache_stale(chat_db):
            logger.debug("AdminCacheMiddleware: refreshing admin cache", chat_id=chat_tid)
            try:
                await update_chat_members(chat_db)
            except Exception as error:  # noqa: BLE001
                logger.warning(
                    "AdminCacheMiddleware: failed to refresh admin cache", chat_id=chat_tid, error=str(error)
                )
        else:
            logger.debug("AdminCacheMiddleware: admin cache is up to date", chat_id=chat_tid)

    async def _is_cache_stale(self, chat: ChatModel) -> bool:
        oldest_admin = await self._get_oldest_admin(chat)
        if oldest_admin is None:
            return True

        cache_age_seconds = (datetime.now(UTC) - oldest_admin.last_updated).total_seconds()
        return cache_age_seconds > CACHE_ADMIN_TTL_SECONDS

    @staticmethod
    async def _get_oldest_admin(chat: ChatModel) -> ChatAdminModel | None:
        return await ChatAdminRepository.get_oldest_admin(chat)
