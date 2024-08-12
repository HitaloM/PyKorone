# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import html
import sys
from traceback import format_exception
from typing import Any

from hydrogram import Client
from hydrogram.errors import ChatWriteForbidden, FloodWait
from hydrogram.types import (
    CallbackQuery,
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    Update,
)
from sentry_sdk import capture_exception

from korone.decorators import router
from korone.handlers.abstract import MessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.logging import logger

IGNORED_EXCEPTIONS: tuple[type[Exception], ...] = (FloodWait, ChatWriteForbidden)


class ErrorsHandler(MessageHandler):
    @router.error()
    async def handle(self, client: Client, update: Update, exception: Exception) -> None:
        if isinstance(exception, IGNORED_EXCEPTIONS):
            return

        etype, value, tb = sys.exc_info()
        if not (etype and value and tb):
            await logger.aerror(
                "[ErrorHandler] Failed to retrieve exception information", exception=exception
            )
            return

        sentry_event_id = self.capture_exception_in_sentry(exception)
        await self.log_exception_to_console(etype, value, tb, sentry_event_id=sentry_event_id)

        chat = self.get_chat_from_update(update)
        if not chat:
            await logger.aerror("[ErrorHandler] Unhandled update type", update=update)
            return

        message_data = self.prepare_error_message(value, sentry_event_id)
        await client.send_message(chat.id, **message_data)

    @staticmethod
    def capture_exception_in_sentry(exception: Exception) -> str | None:
        return capture_exception(exception)

    @staticmethod
    async def log_exception_to_console(
        etype: type, value: BaseException, tb: Any, **kwargs: Any
    ) -> None:
        formatted_exception = format_exception(etype, value, tb)
        await logger.aerror("".join(formatted_exception))
        await logger.aerror("[ErrorHandler] Additional error data", **kwargs)

    @staticmethod
    def format_error_message(exception: BaseException) -> str:
        return " ".join(f"<i>{html.escape(arg)}</i>" for arg in exception.args)

    def prepare_error_message(
        self, exception: BaseException, sentry_event_id: str | None
    ) -> dict[str, Any]:
        text = _("An error occurred while processing this update. :/")
        error_message = self.format_error_message(exception)
        text += f"\n<blockquote>{error_message}</blockquote>\n"

        if sentry_event_id:
            text += _("Reference ID: {id}").format(id=sentry_event_id)

        return {
            "text": text,
            "reply_markup": InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=_("🐞 Report This Error"),
                            url="https://github.com/HitaloM/PyKorone/issues",
                        )
                    ]
                ]
            ),
        }

    @staticmethod
    def get_chat_from_update(update: Update) -> Chat | None:
        if isinstance(update, Message):
            return update.chat
        return update.message.chat if isinstance(update, CallbackQuery) else None
