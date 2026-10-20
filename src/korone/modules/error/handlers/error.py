from typing import TYPE_CHECKING, Any

from aiogram.handlers import ErrorHandler
from aiogram.types import Chat, ErrorEvent, Message

from korone.logger import get_logger
from korone.middlewares.context_data import as_korone_context
from korone.modules.error.utils.backoff import compute_error_signature, should_notify
from korone.modules.error.utils.capture import capture_sentry
from korone.modules.error.utils.error_message import generic_error_message
from korone.modules.error.utils.ignored import QUIET_EXCEPTIONS
from korone.utils.telegram_permissions import handle_no_rights_error, is_no_rights_error

if TYPE_CHECKING:
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

        sentry_event_id = capture_sentry(exception)
        # Explicit capture owns this event; warning logging adds diagnostics without
        # creating a second event through LoggingIntegration.
        await logger.awarning(
            "Unhandled exception",
            exc_info=(type(exception), exception, exception.__traceback__),
            sentry_event_id=sentry_event_id,
        )

        if update and update.inline_query:
            return

        chat = context.get("event_chat")
        if not isinstance(chat, Chat):
            await logger.awarning("Error update has no event chat attached")
            return

        signature = compute_error_signature(exception)
        notify = await should_notify(signature)
        if not notify:
            await logger.ainfo("Suppressing error notification", signature=signature)
            return

        send_kwargs = generic_error_message(exception, sentry_event_id)
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
