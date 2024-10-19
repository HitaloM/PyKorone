from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.types import Message, TelegramObject

from sophie_bot import CONFIG
from sophie_bot.db.models import GreetingsModel


class LeaveUserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # TODO: Handle multiple users add

        if isinstance(event, Message) and event.left_chat_member:
            user_id = event.left_chat_member.id
            chat_id: int = event.chat.id

            # Bot left the chat
            if user_id == CONFIG.bot_id:
                # TODO: Delete chat data?
                raise SkipHandler

            db_item: GreetingsModel = await GreetingsModel.get_by_chat_id(chat_id)

            # Cleanservice
            if db_item.clean_service and db_item.clean_service.enabled:
                await event.delete()

            # Skip handler
            raise SkipHandler

        return await handler(event, data)
