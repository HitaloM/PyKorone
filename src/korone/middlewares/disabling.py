from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.dispatcher.flags import get_flag
from aiogram.types import Message

from korone.db.repositories.disabling import DisablingRepository
from korone.logger import get_logger
from korone.modules.utils_.admin import is_user_admin

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from aiogram.types import TelegramObject

logger = get_logger(__name__)


class DisablingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            chat_id = event.chat.id
            disabled = await DisablingRepository.get_disabled(chat_id)

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
                if is_admin:
                    await logger.adebug("DisablingMiddleware: user is admin; Not skipping!")

        return await handler(event, data)
