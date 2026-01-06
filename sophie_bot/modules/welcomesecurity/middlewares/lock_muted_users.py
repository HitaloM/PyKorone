from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.types import Message, TelegramObject

from sophie_bot.db.models import ChatModel, WSUserModel
from sophie_bot.modules.legacy_modules.utils.user_details import is_user_admin
from sophie_bot.modules.utils_.common_try import common_try
from sophie_bot.utils.logger import log


class LockMutedUsers(BaseMiddleware):
    @staticmethod
    async def _lock_user(message: Message, chat_db: ChatModel, user_db: ChatModel):
        # Delete the message
        await common_try(message.delete())

        # Mute user? Let others know why the message was deleted?
        pass

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and event.from_user and event.chat.type == "private":
            chat_db: ChatModel = data["chat_db"]
            user_db: ChatModel = data["user_db"]

            log.debug("LockMutedUsers", chat=chat_db.tid, user=user_db.tid)

            if await is_user_admin(chat_db.tid, user_db.tid):
                return await handler(event, data)

            model = await WSUserModel.is_user(user_db.iid, chat_db.iid)
            if model and not model.passed:
                await self._lock_user(event, chat_db, user_db)

                # Skip handler
                raise SkipHandler

        return await handler(event, data)
