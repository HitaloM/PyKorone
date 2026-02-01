from typing import TYPE_CHECKING

from aiogram import BaseMiddleware
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.dispatcher.flags import get_flag
from aiogram.types import Message, TelegramObject

from korone.db.repositories import disabling as disabling_repo
from korone.logging import get_logger
from korone.modules.utils_.admin import is_user_admin

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

logger = get_logger(__name__)

type HandlerResult = TelegramObject | bool | None
type MiddlewareDataValue = (
    str | int | float | bool | TelegramObject | list[str] | dict[str, str | int | float | bool | None] | None
)
type MiddlewareData = dict[str, MiddlewareDataValue]


class DisablingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, MiddlewareData], Awaitable[HandlerResult]],
        event: TelegramObject,
        data: MiddlewareData,
    ) -> HandlerResult:
        if isinstance(event, Message):
            chat_id = event.chat.id
            disabled = await disabling_repo.get_disabled(chat_id)

            data["disabled"] = disabled
            await logger.adebug("DisablingMiddleware", chat_id=chat_id, disabled=disabled)

            if handler_disableable := get_flag(data, "disableable"):
                if event.from_user:
                    user_id = event.from_user.id
                    is_admin = await is_user_admin(chat_id, user_id)
                else:
                    is_admin = False

                if handler_disableable["name"] in disabled and not is_admin:
                    await logger.adebug("DisablingMiddleware: disabled; Skipping handler!")
                    raise SkipHandler
                elif is_admin:
                    await logger.adebug("DisablingMiddleware: user is admin; Not skipping!")

        return await handler(event, data)
