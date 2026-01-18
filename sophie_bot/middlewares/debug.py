from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from devtools import Debug

from sophie_bot.utils.logger import log

debug = Debug(highlight=True)


class EventSeparatorMiddleware(BaseMiddleware):
    """Logs a separator line for each new update for easier debugging."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Update):
            user_id = None
            chat_id = None

            # Try to extract user and chat info from various update types
            if event.message:
                user_id = event.message.from_user.id if event.message.from_user else None
                chat_id = event.message.chat.id
            elif event.callback_query:
                user_id = event.callback_query.from_user.id
                chat_id = event.callback_query.message.chat.id if event.callback_query.message else None
            elif event.inline_query:
                user_id = event.inline_query.from_user.id
            elif event.edited_message:
                user_id = event.edited_message.from_user.id if event.edited_message.from_user else None
                chat_id = event.edited_message.chat.id
            elif event.chat_member:
                user_id = event.chat_member.from_user.id
                chat_id = event.chat_member.chat.id
            elif event.my_chat_member:
                user_id = event.my_chat_member.from_user.id
                chat_id = event.my_chat_member.chat.id
            elif event.chat_join_request:
                user_id = event.chat_join_request.from_user.id
                chat_id = event.chat_join_request.chat.id

            info_parts = [f"update_id={event.update_id}"]
            if user_id:
                info_parts.append(f"user={user_id}")
            if chat_id:
                info_parts.append(f"chat={chat_id}")

            # Use cyan color for event separator
            cyan = "\033[36m"
            reset = "\033[0m"
            log.debug(f"{cyan}--- New event: {', '.join(info_parts)} ---{reset}")

        return await handler(event, data)


class UpdateDebugMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        debug(event)
        return await handler(event, data)


class DataDebugMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        debug(data)
        return await handler(event, data)


class HandlerDebugMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        debug(handler)
        result = await handler(event, data)
        debug(result)
        return result
