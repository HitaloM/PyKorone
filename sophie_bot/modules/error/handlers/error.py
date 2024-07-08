import random
import sys
from typing import Any, Dict, Optional, Tuple

import better_exceptions
from aiogram.exceptions import TelegramNetworkError, TelegramRetryAfter
from aiogram.handlers import MessageHandler
from aiogram.types import Chat, InlineKeyboardButton, InlineKeyboardMarkup
from sentry_sdk import capture_exception
from telethon.errors import ChatWriteForbiddenError

from sophie_bot import CONFIG
from sophie_bot.modules.error.utils.haikus import HAIKUS
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.logger import log
from stfu_tg import BlockQuote, Code, Doc, Italic, KeyValue, Title
from stfu_tg.doc import Element

IGNORED_EXCEPTIONS = (
    TelegramNetworkError,
    ChatWriteForbiddenError,
    TelegramRetryAfter
)


class ErrorHandler(MessageHandler):
    async def handle(self) -> Any:
        # We are ignoring the type because I'm sure that aiogram will have this field
        exception = self.event.exception  # type: ignore

        if isinstance(exception, IGNORED_EXCEPTIONS):
            return

        etype, value, tb = sys.exc_info()

        sys_exception = sys.exception()

        sentry_event_id = self.capture_sentry(exception)
        self.log_to_console(etype, value, tb, sentry_event_id=sentry_event_id)

        if not sys_exception:
            log.error("No sys exception", from_aiogram=exception, from_sys=sys_exception)
            return

        elif exception != sys_exception:
            log.error(
                "Mismatched exception seeking",
                from_aiogram=exception,
                from_sys=sys_exception,
            )

        chat: Chat = self.data["event_chat"]

        # Pyright doesn't know that we are returning out of the function if there's no sys_exception
        await self.bot.send_message(chat.id, **self.message_data(sys_exception, sentry_event_id))  # type: ignore

    @staticmethod
    def log_to_console(etype, value, tb, **kwargs):
        formatted_exception = better_exceptions.format_exception(etype, value, tb)
        log.error("".join(formatted_exception))

        log.error("Additional error data", **kwargs)

    @staticmethod
    def capture_sentry(exception: Exception) -> Optional[str]:
        return capture_exception(exception)

    @staticmethod
    def get_error_message(exception: Exception) -> Tuple[str | Element, ...]:
        if isinstance(exception, SophieException):
            # It has 'docs' field
            return exception.docs

        # Return either as itself if the type is based on Core (STFU-able) or stringify as italic
        return tuple(x if isinstance(x, Element) else Italic(str(x)) for x in exception.args)

    def message_data(self, exception: Exception, sentry_event_id: Optional[str]) -> Dict[str, Any]:
        return {
            "text": str(
                Doc(
                    Title(_("😞 I've got an error trying to process this update")),
                    *self.get_error_message(exception),
                    *(
                        ()
                        if isinstance(exception, SophieException)
                        else (
                            " ",
                            BlockQuote(Doc(*random.choice(HAIKUS))),
                        )
                    ),
                    *(
                        (
                            " ",
                            KeyValue(_("Reference ID"), Code(sentry_event_id)),
                        )
                        if sentry_event_id
                        else ()
                    ),
                )
            ),
            "reply_markup": InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text=_("💬 Contact Sophie support"), url=CONFIG.support_link)]]
            ),
        }
