from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.dispatcher.flags import get_flag
from aiogram.types import Message, TelegramObject

from korone.db.models.disabling import DisablingModel
from korone.logging import get_logger
from korone.modules.utils_.admin import is_user_admin

logger = get_logger(__name__)


class DisablingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            chat_id = event.chat.id
            disabled = await DisablingModel.get_disabled(chat_id)

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
