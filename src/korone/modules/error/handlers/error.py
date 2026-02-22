import sys
from typing import TYPE_CHECKING

from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.handlers import ErrorHandler
from aiogram.types import Chat

from korone.logger import get_logger
from korone.modules.error.utils.backoff import compute_error_signature, should_notify
from korone.modules.error.utils.capture import capture_sentry
from korone.modules.error.utils.error_message import generic_error_message
from korone.modules.error.utils.ignored import QUIET_EXCEPTIONS
from korone.modules.error.utils.permission_errors import handle_no_rights_error, is_no_rights_error

if TYPE_CHECKING:
    from types import TracebackType

    from aiogram.types import Update

logger = get_logger(__name__)


class KoroneErrorHandler(ErrorHandler):
    async def handle(self) -> None:
        exception = self.event
        update: Update = self.update

        if isinstance(exception, QUIET_EXCEPTIONS):
            return

        if isinstance(exception, TelegramBadRequest) and is_no_rights_error(exception):
            chat = self.data.get("event_chat")
            await handle_no_rights_error(self.bot, chat, exception)
            return

        etype, value, tb = sys.exc_info()
        sys_exception = sys.exception()

        active_exception = sys_exception if isinstance(sys_exception, Exception) else exception
        sentry_event_id = self.capture_sentry(active_exception)
        self.log_to_console(etype, value, tb, sentry_event_id=sentry_event_id)

        if not isinstance(sys_exception, Exception):
            await logger.awarning("No sys exception", from_aiogram=exception, from_sys=sys_exception)
        elif exception != sys_exception:
            await logger.awarning("Mismatched exception seeking", from_aiogram=exception, from_sys=sys_exception)

        if isinstance(state := self.data.get("state"), FSMContext):
            await state.clear()

        if update and update.inline_query:
            return

        chat = self.data.get("event_chat")
        if not isinstance(chat, Chat):
            await logger.awarning("Error update has no event chat attached")
            return

        signature = compute_error_signature(active_exception)
        notify = await should_notify(signature)
        if not notify:
            await logger.ainfo("Suppressing error notification", signature=signature)
            return

        await self.bot.send_message(chat.id, **generic_error_message(active_exception, sentry_event_id))

    @staticmethod
    def log_to_console(
        etype: type[BaseException] | None,
        value: BaseException | None,
        tb: TracebackType | None,
        **kwargs: str | float | bool | BaseException | None,
    ) -> None:
        if etype and value and tb:
            logger.warning("Unhandled exception", exc_info=(etype, value, tb))
        else:
            logger.warning("Unhandled exception (no sys exc_info available)")
        if kwargs:
            logger.warning("Additional error data", **kwargs)

    @staticmethod
    def capture_sentry(exception: Exception) -> str | None:
        sys_exc = sys.exception()
        if isinstance(sys_exc, Exception):
            return capture_sentry(sys_exc)
        return capture_sentry(exception)
