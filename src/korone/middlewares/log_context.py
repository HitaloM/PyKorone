from typing import TYPE_CHECKING, Any, override

import sentry_sdk
from aiogram import BaseMiddleware
from aiogram.dispatcher.middlewares.user_context import UserContextMiddleware
from aiogram.types import Update
from aiogram.types.update import UpdateTypeLookupError
from structlog.contextvars import bind_contextvars, clear_contextvars

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from aiogram.types.base import TelegramObject


class UpdateLogContextMiddleware(BaseMiddleware):
    @staticmethod
    def _context_from_update(update: Update) -> dict[str, int | str]:
        context: dict[str, int | str] = {"update_id": update.update_id}
        event_context = UserContextMiddleware.resolve_event_context(update)

        if event_context.chat is not None:
            context["chat_id"] = event_context.chat.id
        if event_context.user is not None:
            context["user_id"] = event_context.user.id

        try:
            context["update_type"] = update.event_type
        except UpdateTypeLookupError:
            context["update_type"] = "unknown"

        return context

    @override
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Update):
            return await handler(event, data)

        clear_contextvars()
        context = self._context_from_update(event)
        bind_contextvars(**context)
        try:
            with sentry_sdk.isolation_scope() as scope:
                scope.set_context("telegram_update", context)
                return await handler(event, data)
        finally:
            clear_contextvars()
