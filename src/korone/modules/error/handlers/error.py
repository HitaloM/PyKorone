import sys
from typing import TYPE_CHECKING, Any

from aiogram.fsm.context import FSMContext
from aiogram.handlers import ErrorHandler
from aiogram.types import Chat, ErrorEvent, Message

from korone.logger import get_logger
from korone.middlewares.context_data import as_korone_context
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
        context = as_korone_context(self.data)

        if isinstance(self.event, ErrorEvent):
            exception = self.event.exception
            update = self.event.update
        else:
            event_exception = getattr(self.event, "exception", None)
            exception = event_exception if isinstance(event_exception, Exception) else self.event
            update = self.update

        if isinstance(exception, QUIET_EXCEPTIONS):
            return

        if is_no_rights_error(exception):
            chat = context.get("event_chat")
            handled = await handle_no_rights_error(self.bot, chat, exception)
            if handled:
                return

        etype, value, tb = sys.exc_info()
        sys_exception = sys.exception()

        active_exception = sys_exception if isinstance(sys_exception, Exception) else exception
        sentry_event_id = self.capture_sentry(active_exception)
        await self.log_to_console(etype, value, tb, sentry_event_id=sentry_event_id)

        if not isinstance(sys_exception, Exception):
            await logger.awarning("No sys exception", from_aiogram=exception, from_sys=sys_exception)
        elif type(exception) is not type(sys_exception) or str(exception) != str(sys_exception):
            await logger.awarning("Mismatched exception seeking", from_aiogram=exception, from_sys=sys_exception)

        if isinstance(state := context.get("state"), FSMContext):
            await state.clear()

        if update and update.inline_query:
            return

        chat = context.get("event_chat")
        if not isinstance(chat, Chat):
            await logger.awarning("Error update has no event chat attached")
            return

        signature = compute_error_signature(active_exception)
        notify = await should_notify(signature)
        if not notify:
            await logger.ainfo("Suppressing error notification", signature=signature)
            return

        send_kwargs = generic_error_message(active_exception, sentry_event_id)
        sent_in_origin_message = await self._answer_in_origin_message(update, send_kwargs)
        if sent_in_origin_message:
            return

        await self.bot.send_message(chat.id, **send_kwargs)

    @staticmethod
    def _resolve_origin_message(update: Update | None) -> Message | None:
        if not update:
            return None

        message_candidates = (
            update.message,
            update.edited_message,
            update.channel_post,
            update.edited_channel_post,
            update.business_message,
            update.edited_business_message,
        )

        for message in message_candidates:
            if isinstance(message, Message):
                return message

        callback_query = update.callback_query
        if callback_query:
            callback_message = callback_query.message
            if isinstance(callback_message, Message):
                return callback_message

        return None

    @classmethod
    async def _answer_in_origin_message(cls, update: Update | None, send_kwargs: dict[str, Any]) -> bool:
        origin_message = cls._resolve_origin_message(update)
        if not origin_message:
            return False

        await origin_message.answer(**send_kwargs)
        return True

    @staticmethod
    async def log_to_console(
        etype: type[BaseException] | None,
        value: BaseException | None,
        tb: TracebackType | None,
        **kwargs: str | float | bool | BaseException | None,
    ) -> None:
        if etype and value and tb:
            await logger.awarning("Unhandled exception", exc_info=(etype, value, tb))
        else:
            await logger.awarning("Unhandled exception (no sys exc_info available)")
        if kwargs:
            await logger.awarning("Additional error data", **kwargs)

    @staticmethod
    def capture_sentry(exception: Exception) -> str | None:
        sys_exc = sys.exception()
        if isinstance(sys_exc, Exception):
            return capture_sentry(sys_exc)
        return capture_sentry(exception)
