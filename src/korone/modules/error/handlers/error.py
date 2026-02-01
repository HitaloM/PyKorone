from __future__ import annotations

import sys
from typing import TYPE_CHECKING, cast

from aiogram.handlers import ErrorHandler

from korone.logging import get_logger
from korone.modules.error.utils.backoff import compute_error_signature, should_notify
from korone.modules.error.utils.error_message import generic_error_message
from korone.modules.error.utils.ignored import QUIET_EXCEPTIONS

if TYPE_CHECKING:
    from types import TracebackType

    from aiogram.types import Chat, Update
    from aiogram.types.error_event import ErrorEvent

logger = get_logger(__name__)


class KoroneErrorHandler(ErrorHandler):
    async def handle(self) -> None:
        error_event = cast("ErrorEvent", self.event)
        exception: BaseException = error_event.exception
        update: Update = error_event.update

        if isinstance(exception, QUIET_EXCEPTIONS):
            return

        etype, value, tb = sys.exc_info()

        sys_exception = sys.exception()

        self.log_to_console(etype, value, tb)

        if not sys_exception:
            await logger.aerror("No sys exception", from_aiogram=exception, from_sys=sys_exception)
            return

        if exception != sys_exception:
            await logger.aerror("Mismatched exception seeking", from_aiogram=exception, from_sys=sys_exception)
        try:
            await self.data["state"].clear()
        except Exception as err:  # noqa: BLE001
            await logger.aerror("Failed to clear state", err=err)

        if update.inline_query:
            return

        chat: Chat = self.data["event_chat"]

        signature = compute_error_signature(sys_exception)
        notify = await should_notify(signature)
        if not notify:
            await logger.ainfo("Suppressing error notification", signature=signature)
            return

        if isinstance(sys_exception, Exception):
            error_payload = generic_error_message(sys_exception, hide_contact=False)
            await self.bot.send_message(chat.id, text=error_payload["text"])

    @staticmethod
    def log_to_console(
        etype: type[BaseException] | None,
        value: BaseException | None,
        tb: TracebackType | None,
        **kwargs: str | float | bool | BaseException | None,
    ) -> None:
        if etype is not None and value is not None and tb is not None:
            logger.error("Unhandled exception", exc_info=(etype, value, tb))
        else:
            logger.error("Unhandled exception (no sys exc_info available)")
        if kwargs:
            logger.error("Additional error data", **kwargs)
